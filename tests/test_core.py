import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from oru import complaint as C, crop, labels, store  # noqa: E402


def test_suggest_issue():
    assert C.suggest_issue("big pothole on the road") == "road"
    assert C.suggest_issue("தெருவில் குப்பை குவிந்துள்ளது") == "garbage"
    assert C.suggest_issue("power cut since morning") == "electric"
    assert C.suggest_issue("hello") is None


def test_routes():
    r = C.route("water", "chennai")
    assert r["helplines"][0]["number"] == "1916"
    r = C.route("road", "chennai")
    assert r["helplines"][0]["number"] == "1913"
    r = C.route("electric", "village")
    assert r["helplines"][0]["number"] == "94987 94987"
    # other cities have no helpline of their own -> CM helpline fallback
    r = C.route("garbage", "city")
    assert r["helplines"][0]["number"] == "1100"
    # village drainage falls back to the BDO office
    assert "Block Development" in C.route("drainage", "village")["en"]


def test_every_issue_routes_everywhere():
    for it in C.issues():
        for area in ("chennai", "city", "village"):
            assert C.route(it["id"], area)["en"]


def test_letters():
    c = C.Complaint("road", "chennai", address="Gandhi Street, Chrompet", landmark="near the temple",
                    name="Arjun", phone="9XXXXXXXXX", has_photo=True)
    en = C.build_letter(c, "en", date(2026, 10, 21))
    ta = C.build_letter(c, "ta", date(2026, 10, 21))
    assert "Greater Chennai Corporation" in en and "21/10/2026" in en and "near the temple" in en
    assert "photograph" in en and "{" not in en
    assert "பெருநகர சென்னை மாநகராட்சி" in ta and "இணைக்கப்பட்டுள்ளது" in ta and "{" not in ta
    c2 = C.Complaint("electric", "city", town="Salem", address="Anna Nagar", name="Raja")
    assert "Salem" in C.build_letter(c2, "en") and "TNPDCL" in C.build_letter(c2, "en")


def test_store(tmp_path):
    s = store.Store(tmp_path / "t.db")
    cid = s.add("road", "chennai", "Chrompet", "en", "letter")
    assert s.all()[0]["status"] == "draft"
    s.set_status(cid, "sent")
    assert s.get(cid)["status"] == "sent"
    s.delete(cid)
    assert s.all() == []


def test_remedies_complete():
    for cr in crop.crops():
        ds = crop.diseases_for(cr["id"])
        assert ds
        for d in ds:
            for k in ("name_ta", "name_en", "symptoms_ta", "symptoms_en"):
                assert d[k]
            for k in ("action_ta", "action_en", "prevent_ta", "prevent_en"):
                assert len(d[k]) >= 2


def test_predictor_with_dummy_model(tmp_path):
    import json
    import numpy as np
    import onnx
    from onnx import TensorProto, helper, numpy_helper
    from PIL import Image
    labels = ["tomato_early_blight", "healthy_tomato", "rice_blast"]
    w = numpy_helper.from_array(np.array([[3, 0, 0], [0, 0, 0], [0, 0, 0]], dtype=np.float32), "W")
    nodes = [helper.make_node("ReduceMean", ["x"], ["m"], axes=[2, 3], keepdims=0),
             helper.make_node("MatMul", ["m", "W"], ["y"])]
    g = helper.make_graph(nodes, "g", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, 224, 224])],
                          [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 3])], [w])
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8
    onnx.save(m, str(tmp_path / "crop_model.onnx"))
    (tmp_path / "crop_labels.json").write_text(json.dumps({"labels": labels}))
    Image.new("RGB", (300, 200), (200, 30, 30)).save(tmp_path / "leaf.png")
    p = crop.CropPredictor.load(tmp_path)
    assert p is not None
    res = p.predict(str(tmp_path / "leaf.png"))
    assert len(res) == 3 and abs(sum(r[1] for r in res) - 1) < 1e-4
    assert crop.CropPredictor.load(tmp_path / "missing") is None


def test_label_interpretation():
    r = labels.interpret("Tomato___Late_blight")
    assert (r.kind, r.disease_id) == ("disease", "tomato_late_blight")
    assert labels.interpret("Tomato___Tomato_Yellow_Leaf_Curl_Virus").disease_id == "tomato_leaf_curl"
    assert labels.interpret("Tomato___Spider_mites Two-spotted_spider_mite").disease_id == "tomato_spider_mites"
    assert labels.interpret("Tomato___Septoria_leaf_spot").disease_id == "tomato_septoria_leaf_spot"
    assert labels.interpret("Tomato___Leaf_Mold").disease_id == "tomato_leaf_mold"
    assert labels.interpret("Tomato___Target_Spot").disease_id == "tomato_target_spot"
    assert labels.interpret("Tomato___Tomato_mosaic_virus").disease_id == "tomato_mosaic_virus"
    assert labels.interpret("Tomato___Bacterial_spot").disease_id == "tomato_bacterial_spot"
    assert labels.interpret("Potato___Early_blight").disease_id == "potato_early_blight"
    assert labels.interpret("Potato___healthy").kind == "healthy"
    o = labels.interpret("Apple___Apple_scab")
    assert o.kind == "other" and o.pretty == "Apple - Apple scab"


def test_every_mapped_label_exists_in_library():
    for _, _, did in labels.RULES:
        assert crop.disease(did) is not None, did


def test_predictor_resize_and_config(tmp_path):
    import json
    import numpy as np
    import onnx
    from onnx import TensorProto, helper, numpy_helper
    from PIL import Image
    w = numpy_helper.from_array(np.array([[0, 5], [0, 0], [0, 0]], dtype=np.float32), "W")
    nodes = [helper.make_node("ReduceMean", ["x"], ["m"], axes=[2, 3], keepdims=0), helper.make_node("MatMul", ["m", "W"], ["y"])]
    g = helper.make_graph(nodes, "g", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, 224, 224])],
                          [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 2])], [w])
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8
    onnx.save(m, str(tmp_path / "crop_model.onnx"))
    (tmp_path / "crop_labels.json").write_text(json.dumps(
        {"labels": ["Tomato___healthy", "Tomato___Late_blight"], "mean": [0.5] * 3, "std": [0.5] * 3, "size": 224, "resize": 256}))
    Image.new("RGB", (640, 480), (250, 250, 250)).save(tmp_path / "leaf.jpg")
    p = crop.CropPredictor.load(tmp_path)
    assert p.resize == 256 and p.mean == [0.5] * 3
    x = p._prepare(str(tmp_path / "leaf.jpg"))
    assert x.shape == (1, 3, 224, 224)
    top = p.predict(str(tmp_path / "leaf.jpg"))
    assert top[0][0] == "Tomato___Late_blight" and top[0][1] > 0.9
