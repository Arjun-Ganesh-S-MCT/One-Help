package com.oruudhavi.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.BeforeClass
import org.junit.Test
import java.io.File

/** The Kotlin logic must give exactly the same results as the Python app (parity.json is made from the Python code). */
class ParityTest {
    companion object {
        lateinit var parity: JSONObject
        private fun find(name: String): File {
            var d: File? = File("").absoluteFile
            while (d != null) {
                for (p in listOf("app/src/main/assets/$name", "src/main/assets/$name")) { val f = File(d, p); if (f.exists()) return f }
                d = d.parentFile
            }
            error("$name not found")
        }
        @BeforeClass @JvmStatic fun setup() {
            Data.load(find("data.json").readText())
            parity = JSONObject(ParityTest::class.java.getResource("/parity.json")!!.readText())
        }
    }

    @Test fun letters() {
        val (y, m, d) = parity.getString("today").split("-").map { it.toInt() }
        val arr = parity.getJSONArray("letters")
        assertEquals(144, arr.length())
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i); val c = o.getJSONObject("c")
            val cc = Complaint(c.getString("issue_id"), c.getString("area"), c.getString("town"), c.getString("address"),
                c.getString("landmark"), c.getString("name"), c.getString("phone"), c.getString("extra"), c.getBoolean("has_photo"))
            assertEquals("letter #$i", o.getString("letter"), Logic.buildLetter(cc, o.getString("lang"), d, m, y))
        }
    }

    @Test fun routes() {
        val arr = parity.getJSONArray("routes")
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i); val r = o.getJSONObject("route")
            val got = Logic.route(o.getString("issue"), o.getString("area"))
            assertEquals(r.getString("en"), got.en); assertEquals(r.getString("ta"), got.ta)
            assertEquals(r.getJSONArray("helplines").length(), got.helplines.size)
            r.getJSONArray("helplines").objs().forEachIndexed { k, h -> assertEquals(h.getString("number"), got.helplines[k].number) }
        }
    }

    @Test fun suggestions() {
        val arr = parity.getJSONArray("suggest")
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            assertEquals(o.getString("text"), if (o.isNull("id")) null else o.getString("id"), Logic.suggestIssue(o.getString("text")))
        }
    }

    @Test fun labels() {
        val arr = parity.getJSONArray("labels")
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i); val r = o.getJSONObject("reading")
            val got = Logic.interpret(o.getString("raw"))
            assertEquals(o.getString("raw"), r.getString("kind"), got.kind)
            assertEquals(r.getString("diseaseId"), got.diseaseId); assertEquals(r.getString("pretty"), got.pretty)
        }
    }

    @Test fun sixtyPercentRule() {
        assertEquals("unsure", Logic.decide("Tomato___Late_blight", 0.59f).kind)
        assertEquals("disease", Logic.decide("Tomato___Late_blight", 0.6f).kind)
        assertNotNull(Data.disease("tomato_late_blight"))
    }
}
