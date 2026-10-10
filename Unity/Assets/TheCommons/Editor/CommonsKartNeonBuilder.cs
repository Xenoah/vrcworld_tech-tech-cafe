#if UNITY_EDITOR
using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;

// v0.11: Neo-Tokyo neon dressing for APEX / NEON SWITCHYARD, built from
// Data/kart_neon_layout.json (placed and checked by Blender/build_kart_neon_layout.py).
// Everything is visual only (no colliders, except the vending machines on the
// south walkway) and stays clear of every deck, the pit, the tyres and walls.
// The kart meshes, colliders and course sources are untouched. Emissive parts
// contribute baked glow (scale in lightmap 0: they light the floor but use probes).
public static partial class CommonsExperienceBuilder
{
    [Serializable] public class NeonLayout { public string version; public NeonTree[] trees; public NeonGate[] torii; public NeonGate pass_arch; public NeonString[] lanterns; public NeonTower tower; public NeonSign[] hanging_signs, wall_signs; public NeonVending[] vending; }
    [Serializable] public class NeonTree { public string type, hairpin; public float[] position; public float radius, height, yaw; }
    [Serializable] public class NeonGate { public float[] position, banner; public float road_y, yaw, post_offset, rise, station; public string texture; }
    [Serializable] public class NeonString { public float[] from, to; public float pole_height; public int lanterns; }
    [Serializable] public class NeonTower { public float[] position; public float height, @base; }
    [Serializable] public class NeonSign { public string texture; public float[] position, size; public float yaw; }
    [Serializable] public class NeonVending { public float[] position; public float yaw; public int variant; }

    static Transform neonRoot;
    static Dictionary<string, Material> neonCache;

    static void BuildKartNeon()
    {
        string path = Root + "/Data/kart_neon_layout.json";
        if (!File.Exists(path)) { Debug.LogWarning("THE COMMONS: kart_neon_layout.json missing; kart neon dressing skipped."); return; }
        NeonLayout L = JsonUtility.FromJson<NeonLayout>(File.ReadAllText(path));
        neonRoot = new GameObject("ATTR_KartNeon").transform; neonCache = new Dictionary<string, Material>(); meshCache = new Dictionary<string, Mesh>();
        int built = 0;
        if (L.trees != null) for (int i = 0; i < L.trees.Length; i++)
            {
                // Quest keeps every hairpin's feature tree and half of the forest.
                if (Mobile && L.trees[i].hairpin == null && i % 2 == 1) continue;
                NeonTreeObject(L.trees[i]); built++;
            }
        if (L.torii != null) foreach (NeonGate g in L.torii) Torii(g);
        if (L.pass_arch != null && !string.IsNullOrEmpty(L.pass_arch.texture)) PassArch(L.pass_arch);
        if (L.lanterns != null) foreach (NeonString s in L.lanterns) LanternString(s);
        if (L.tower != null && L.tower.position != null && L.tower.position.Length == 3) RadioTower(L.tower);
        if (L.wall_signs != null) foreach (NeonSign s in L.wall_signs) WallSign(s, false);
        if (L.hanging_signs != null) foreach (NeonSign s in L.hanging_signs) WallSign(s, true);
        if (L.vending != null) foreach (NeonVending v in L.vending) VendingMachine(v);
        Debug.Log("THE COMMONS kart neon: " + built + " trees, " + (L.torii == null ? 0 : L.torii.Length) + " torii, " + (L.wall_signs == null ? 0 : L.wall_signs.Length) + " wall signs.");
    }

    // ------------------------------------------------------------ materials
    static Material NeonMat(string key, Color color, float strength, float albedo = .18f)
    {
        if (neonCache.ContainsKey(key)) return neonCache[key];
        Material m = new Material(Shader.Find(Mobile ? "The Commons/Flat Light" : "The Commons/Surface")); m.name = "NEON_" + key; m.enableInstancing = true;
        m.SetColor("_Color", color * albedo); m.SetColor("_EmissionColor", color * strength);
        if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", .5f);
        m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
        Save(m, "Materials", ".mat"); emissive.Add(m); neonCache[key] = m; return m;
    }
    static Material DarkMat(string key, Color color)
    {
        if (neonCache.ContainsKey(key)) return neonCache[key];
        Material m = new Material(Shader.Find(Mobile ? "The Commons/Flat Light" : "The Commons/Surface")); m.name = "NEON_" + key; m.enableInstancing = true;
        m.SetColor("_Color", color); m.SetColor("_EmissionColor", Color.black);
        if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", .35f);
        Save(m, "Materials", ".mat"); neonCache[key] = m; return m;
    }
    static Material ShellMat(string key, Color color)
    {
        if (neonCache.ContainsKey(key)) return neonCache[key];
        // Few, bright grid lines read as neon tubes over the dark canopy.
        Material m = Holo("Neon" + key, color, .75f, new Vector2(12, 6), 0, 0, .05f); neonCache[key] = m; return m;
    }
    static Material SignMat(string texture)
    {
        if (neonCache.ContainsKey(texture)) return neonCache[texture];
        Material m = new Material(Shader.Find("The Commons/Media")); m.name = "NEON_" + texture;
        m.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Media/Neon/" + texture + ".png");
        if (m.mainTexture == null) Debug.LogWarning("THE COMMONS: missing neon texture " + texture);
        m.SetColor("_Color", new Color(1.15f, 1.15f, 1.15f, 1f)); Save(m, "Materials", ".mat"); neonCache[texture] = m; return m;
    }
    static Color Rgb(float r, float g, float b) { return new Color(r, g, b, 1f); }

    // ------------------------------------------------------------- helpers
    static GameObject NeonPrim(PrimitiveType type, string name, Transform parent, Vector3 local, Vector3 scale, Material material, Quaternion rotation, bool glow)
    {
        GameObject o = Prim(type, name, parent, local, scale, material, rotation);
        Decor(o, glow); return o;
    }
    static void Decor(GameObject o, bool glow)
    {
        Renderer r = o.GetComponent<Renderer>();
        if (glow)
        {
            // Emits into the baked lightmap but is itself lit by probes.
            GameObjectUtility.SetStaticEditorFlags(o, StaticEditorFlags.ContributeGI | StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
            if (r is MeshRenderer) ((MeshRenderer)r).scaleInLightmap = 0f;
        }
        else GameObjectUtility.SetStaticEditorFlags(o, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
    }
    static Mesh Cone(string name, float radius, float height, int segments)
    {
        string key = "Cone_" + name; Mesh m = new Mesh(); m.name = "EXP_" + key;
        Vector3[] v = new Vector3[segments * 2 + 2]; Vector2[] uv = new Vector2[v.Length]; int[] tri = new int[segments * 6];
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments;
            v[i] = new Vector3(Mathf.Cos(a) * radius, 0, Mathf.Sin(a) * radius); uv[i] = new Vector2(i / (float)segments, 0);
            v[segments + 1 + i] = new Vector3(0, height, 0); uv[segments + 1 + i] = new Vector2(i / (float)segments, 1);
        }
        for (int i = 0; i < segments; i++) { tri[i * 3] = i; tri[i * 3 + 1] = segments + 1 + i; tri[i * 3 + 2] = i + 1; }
        for (int i = 0; i < segments - 2; i++) { int k = segments * 3 + i * 3; tri[k] = 0; tri[k + 1] = i + 1; tri[k + 2] = i + 2; }
        Array.Resize(ref tri, segments * 3 + (segments - 2) * 3);
        m.vertices = v; m.uv = uv; m.triangles = tri; m.RecalculateNormals(); m.RecalculateBounds();
        Unwrapping.GenerateSecondaryUVSet(m); Save(m, "Meshes", ".asset"); return m;
    }
    static Dictionary<string, Mesh> meshCache = new Dictionary<string, Mesh>();
    static Mesh Cached(string key, Func<Mesh> make) { if (!meshCache.ContainsKey(key) || meshCache[key] == null) meshCache[key] = make(); return meshCache[key]; }
    static void Bar(Transform parent, Vector3 a, Vector3 b, float thickness, Material material, bool glow)
    {
        Vector3 d = b - a; if (d.sqrMagnitude < 1e-6f) return;
        GameObject o = Prim(PrimitiveType.Cube, "Bar", parent, Vector3.zero, new Vector3(thickness, thickness, d.magnitude), material, Quaternion.identity);
        o.transform.position = (a + b) * .5f; o.transform.rotation = Quaternion.LookRotation(d); Decor(o, glow);
    }

    // --------------------------------------------------------------- trees
    static void NeonTreeObject(NeonTree t)
    {
        Transform tree = new GameObject("NeonTree_" + t.type + (t.hairpin == null ? "" : "_" + t.hairpin)).transform; tree.SetParent(neonRoot, false);
        tree.position = P(t.position); tree.rotation = Quaternion.Euler(0, t.yaw, 0);
        float h = t.height, r = t.radius;
        Material trunk = DarkMat("Trunk", Rgb(.05f, .05f, .08f));
        Color neon = t.type == "cedar" ? Rgb(.05f, 1f, .6f) : t.type == "sakura" ? Rgb(1f, .2f, .6f) : Rgb(1f, .22f, .04f);
        Color edge = t.type == "cedar" ? Rgb(.2f, .7f, 1f) : t.type == "sakura" ? Rgb(1f, .6f, .85f) : Rgb(1f, .08f, .06f);
        Material core = NeonMat(t.type + "Core", neon, .28f, .07f), ring = NeonMat(t.type + "Ring", edge, 3.2f), shell = ShellMat(t.type, neon);
        Material ground = NeonMat(t.type + "Ground", neon, 2.2f);
        Decor(MeshObject("Planter", tree, Cached("Planter_" + t.type + r.ToString("0.0"), () => Annulus("NeonPlanter_" + t.type + "_" + r.ToString("0.0"), r * .55f, r * .62f, 40)), ground, tree.position + Vector3.up * .015f, Quaternion.identity), true);
        if (t.type == "cedar")
        {
            NeonPrim(PrimitiveType.Cylinder, "Trunk", tree, new Vector3(0, h * .17f, 0), new Vector3(.3f, h * .17f, .3f), trunk, Quaternion.identity, false);
            float[] baseY = { h * .25f, h * .45f, h * .65f }, rad = { r, r * .75f, r * .5f }, ht = { h * .45f, h * .4f, h * .35f };
            for (int k = 0; k < 3; k++)
            {
                string key = "Cedar_" + rad[k].ToString("0.00") + "_" + ht[k].ToString("0.00");
                Mesh cone = Cached(key, () => Cone(key, rad[k], ht[k], 12));
                Decor(MeshObject("Canopy", tree, cone, core, tree.position + Vector3.up * baseY[k], tree.rotation), true);
                GameObject coneShell = MeshObject("Shell", tree, cone, shell, tree.position + Vector3.up * (baseY[k] - .02f), tree.rotation);
                coneShell.transform.localScale = Vector3.one * 1.06f; Decor(coneShell, false);
                Decor(MeshObject("NeonRing", tree, Cached("Ring" + key, () => Torus("NeonRing_" + key, rad[k] * 1.02f, .04f, 36, 5)), ring, tree.position + Vector3.up * (baseY[k] + .03f), tree.rotation), true);
            }
        }
        else
        {
            NeonPrim(PrimitiveType.Cylinder, "Trunk", tree, new Vector3(0, h * .25f, 0), new Vector3(.26f, h * .25f, .26f), trunk, Quaternion.identity, false);
            NeonPrim(PrimitiveType.Cylinder, "Branch", tree, new Vector3(r * .22f, h * .52f, 0), new Vector3(.12f, h * .12f, .12f), trunk, Quaternion.Euler(0, 0, -35), false);
            Vector3[] blobs = { new Vector3(0, h * .7f, 0), new Vector3(r * .55f, h * .62f, r * .2f), new Vector3(-r * .5f, h * .6f, -r * .25f), new Vector3(r * .1f, h * .62f, -r * .55f) };
            float[] size = { r * 1.5f, r * 1.05f, r * 1.0f, r * .95f };
            for (int k = 0; k < blobs.Length; k++)
            {
                NeonPrim(PrimitiveType.Sphere, "Canopy", tree, blobs[k], Vector3.one * size[k], core, Quaternion.identity, true);
                NeonPrim(PrimitiveType.Sphere, "Shell", tree, blobs[k], Vector3.one * size[k] * 1.07f, shell, Quaternion.identity, false);
            }
            Decor(MeshObject("Halo", tree, Cached("Halo" + t.type + r.ToString("0.0"), () => Torus("NeonHalo_" + t.type + "_" + r.ToString("0.0"), r * 1.05f, .035f, 48, 5)), ring, tree.position + Vector3.up * h * .66f, tree.rotation * Quaternion.Euler(8, 0, 4)), true);
        }
    }

    // --------------------------------------------------------------- gates
    static void GateFrame(Transform parent, NeonGate g, Material post, Material beam, Material cap, bool torii)
    {
        float top = g.road_y + g.rise; float half = g.post_offset;
        for (int side = -1; side <= 1; side += 2)
            NeonPrim(PrimitiveType.Cylinder, "Post", parent, new Vector3(side * half, (top - .2f) * .5f, 0), new Vector3(.36f, (top - .2f) * .5f, .36f), post, Quaternion.identity, true);
        if (!torii) return;
        NeonPrim(PrimitiveType.Cube, "Kasagi", parent, new Vector3(0, top, 0), new Vector3(half * 2f + 1.5f, .32f, .44f), beam, Quaternion.identity, true);
        NeonPrim(PrimitiveType.Cube, "KasagiCap", parent, new Vector3(0, top + .2f, 0), new Vector3(half * 2f + 1.7f, .1f, .5f), cap, Quaternion.identity, false);
        NeonPrim(PrimitiveType.Cube, "Nuki", parent, new Vector3(0, top - 1.05f, 0), new Vector3(half * 2f + .7f, .24f, .26f), beam, Quaternion.identity, true);
        NeonPrim(PrimitiveType.Cube, "Gakuzuka", parent, new Vector3(0, top - .52f, 0), new Vector3(.22f, .8f, .2f), beam, Quaternion.identity, true);
    }
    static void Torii(NeonGate g)
    {
        Transform t = new GameObject("NeonTorii_" + g.station.ToString("0")).transform; t.SetParent(neonRoot, false);
        t.position = P(g.position); t.rotation = Quaternion.Euler(0, g.yaw, 0);   // local X spans the road, karts pass along local Z
        Material vermilion = NeonMat("Vermilion", Rgb(1f, .14f, .04f), 1.35f), black = DarkMat("ToriiCap", Rgb(.03f, .03f, .04f));
        GateFrame(t, g, vermilion, vermilion, black, true);
    }
    static void PassArch(NeonGate g)
    {
        Transform t = new GameObject("NeonPassGate").transform; t.SetParent(neonRoot, false);
        t.position = P(g.position); t.rotation = Quaternion.Euler(0, g.yaw, 0);
        Material steel = DarkMat("GateSteel", Rgb(.12f, .13f, .17f)), amber = NeonMat("Amber", Rgb(1f, .62f, .12f), 3.2f);
        GateFrame(t, g, steel, steel, steel, false);
        float w = g.banner != null && g.banner.Length == 2 ? g.banner[0] : 5.6f, h = g.banner != null && g.banner.Length == 2 ? g.banner[1] : 1.75f;
        float cy = g.road_y + g.rise + h * .5f;
        NeonPrim(PrimitiveType.Cube, "Beam", t, new Vector3(0, cy, 0), new Vector3(g.post_offset * 2f + .4f, .18f, .2f), steel, Quaternion.identity, false);
        NeonPrim(PrimitiveType.Cube, "Board", t, new Vector3(0, cy, 0), new Vector3(w, h, .1f), DarkMat("Board", Rgb(.02f, .02f, .03f)), Quaternion.identity, false);
        Material sign = SignMat(g.texture);
        // Both faces readable: approaching karts see the front, the climb back sees the rear.
        foreach (float face in new[] { -1f, 1f })
        {
            GameObject q = CommonsWorldBuilder.Quad("NeonPassBanner", Vector3.zero, w, h, 0, sign); q.transform.SetParent(t, false);
            // Quad faces local -Z: the -Z quad keeps rotation 0, the +Z quad turns 180.
            q.transform.localPosition = new Vector3(0, cy, face * .056f); q.transform.localRotation = Quaternion.Euler(0, face < 0 ? 0f : 180f, 0); Decor(q, false);
        }
        foreach (float y in new[] { cy - h * .5f - .06f, cy + h * .5f + .06f })
            NeonPrim(PrimitiveType.Cube, "Tube", t, new Vector3(0, y, 0), new Vector3(w + .1f, .06f, .14f), amber, Quaternion.identity, true);
    }

    // ------------------------------------------------------------ lanterns
    static void LanternString(NeonString s)
    {
        Transform t = new GameObject("NeonLanterns").transform; t.SetParent(neonRoot, false);
        Vector3 a = P(s.from), b = P(s.to);
        Material pole = DarkMat("Pole", Rgb(.08f, .08f, .1f)), red = NeonMat("LanternRed", Rgb(1f, .16f, .1f), 2.6f), white = NeonMat("LanternWhite", Rgb(1f, .85f, .65f), 2.4f);
        Material wire = DarkMat("Wire", Rgb(.02f, .02f, .02f));
        foreach (Vector3 p in new[] { a, b })
        {
            GameObject o = Prim(PrimitiveType.Cylinder, "Pole", t, Vector3.zero, new Vector3(.12f, s.pole_height * .5f, .12f), pole, Quaternion.identity);
            o.transform.position = p + Vector3.up * s.pole_height * .5f; Decor(o, false);
        }
        int n = Mathf.Max(3, s.lanterns); Vector3 prev = a + Vector3.up * s.pole_height;
        for (int i = 1; i <= n + 1; i++)
        {
            float u = i / (float)(n + 1);
            Vector3 p = Vector3.Lerp(a, b, u) + Vector3.up * (s.pole_height - .55f * 4f * u * (1f - u));
            Bar(t, prev, p, .02f, wire, false); prev = p;
            if (i == n + 1) break;
            GameObject l = Prim(PrimitiveType.Sphere, "Chochin", t, Vector3.zero, new Vector3(.34f, .46f, .34f), i % 3 == 0 ? white : red, Quaternion.identity);
            l.transform.position = p - Vector3.up * .3f; Decor(l, true);
            foreach (float dy in new[] { -.24f, .24f })
            {
                GameObject c = Prim(PrimitiveType.Cylinder, "Cap", t, Vector3.zero, new Vector3(.2f, .025f, .2f), wire, Quaternion.identity);
                c.transform.position = p - Vector3.up * .3f + Vector3.up * dy; Decor(c, false);
            }
        }
    }

    // --------------------------------------------------------------- tower
    static void RadioTower(NeonTower w)
    {
        Transform t = new GameObject("NeonRadioTower").transform; t.SetParent(neonRoot, false); t.position = P(w.position);
        Material red = NeonMat("TowerRed", Rgb(1f, .26f, .08f), 3.0f), white = NeonMat("TowerWhite", Rgb(.9f, .95f, 1f), 2.6f), dark = DarkMat("TowerSteel", Rgb(.1f, .1f, .13f));
        float H = w.height, B = w.@base * .5f, T = .5f;
        Vector3 o = t.position;
        Func<float, float> half = y => Mathf.Lerp(B, T, Mathf.Pow(y / H, .8f));
        for (int sx = -1; sx <= 1; sx += 2) for (int sz = -1; sz <= 1; sz += 2)
                Bar(t, o + new Vector3(sx * B, 0, sz * B), o + new Vector3(sx * T, H, sz * T), .22f, dark, false);
        float[] levels = { 2.4f, 4.8f, 7.2f, 9.4f, 11.2f };
        for (int k = 0; k < levels.Length; k++)
        {
            float y = levels[k], s = half(y); Material m = k % 2 == 0 ? red : white;
            Vector3[] c = { o + new Vector3(-s, y, -s), o + new Vector3(s, y, -s), o + new Vector3(s, y, s), o + new Vector3(-s, y, s) };
            for (int e = 0; e < 4; e++) Bar(t, c[e], c[(e + 1) % 4], .12f, m, true);
            if (Mobile) continue;
            float y0 = k == 0 ? 0f : levels[k - 1], s0 = half(y0);
            for (int e = 0; e < 4; e++)
            {
                Vector3 a0 = o + Corner(e, s0, y0), a1 = o + Corner(e + 1, s0, y0), b0 = o + Corner(e, s, y), b1 = o + Corner(e + 1, s, y);
                Bar(t, a0, b1, .05f, k % 2 == 0 ? white : red, true); Bar(t, a1, b0, .05f, k % 2 == 0 ? white : red, true);
            }
        }
        float deckY = 7.2f, ds = half(deckY) + .45f;
        NeonPrim(PrimitiveType.Cube, "Observatory", t, new Vector3(0, deckY + .45f, 0), new Vector3(ds * 2f, .9f, ds * 2f), dark, Quaternion.identity, false);
        NeonPrim(PrimitiveType.Cube, "ObservatoryBand", t, new Vector3(0, deckY + .45f, 0), new Vector3(ds * 2f + .04f, .16f, ds * 2f + .04f), white, Quaternion.identity, true);
        NeonPrim(PrimitiveType.Cylinder, "Antenna", t, new Vector3(0, H + .7f, 0), new Vector3(.12f, .7f, .12f), red, Quaternion.identity, true);
    }
    static Vector3 Corner(int e, float s, float y)
    {
        e = ((e % 4) + 4) % 4;
        return e == 0 ? new Vector3(-s, y, -s) : e == 1 ? new Vector3(s, y, -s) : e == 2 ? new Vector3(s, y, s) : new Vector3(-s, y, s);
    }

    // --------------------------------------------------------------- signs
    static void WallSign(NeonSign s, bool hanging)
    {
        Transform t = new GameObject((hanging ? "NeonHanging_" : "NeonWall_") + s.texture).transform; t.SetParent(neonRoot, false);
        t.position = P(s.position); t.rotation = Quaternion.Euler(0, s.yaw, 0);
        float w = s.size[0], h = s.size[1]; Material sign = SignMat(s.texture);
        NeonPrim(PrimitiveType.Cube, "Backing", t, new Vector3(0, 0, hanging ? 0f : .07f), new Vector3(w + .16f, h + .16f, hanging ? .06f : .1f), DarkMat("Board", Rgb(.02f, .02f, .03f)), Quaternion.identity, false);
        foreach (float face in hanging ? new[] { -1f, 1f } : new[] { -1f })
        {
            GameObject q = CommonsWorldBuilder.Quad("NeonSign", Vector3.zero, w, h, 0, sign); q.transform.SetParent(t, false);
            q.transform.localPosition = new Vector3(0, 0, face * .04f); q.transform.localRotation = Quaternion.Euler(0, face < 0 ? 0f : 180f, 0); Decor(q, false);
        }
        if (!hanging) return;
        Material wire = DarkMat("Wire", Rgb(.02f, .02f, .02f));
        foreach (float x in new[] { -w * .4f, w * .4f })
        {
            float len = Mathf.Max(.2f, 14.1f - (t.position.y + h * .5f));
            NeonPrim(PrimitiveType.Cylinder, "Hanger", t, new Vector3(x, h * .5f + len * .5f, 0), new Vector3(.03f, len * .5f, .03f), wire, Quaternion.identity, false);
        }
    }
    static void VendingMachine(NeonVending v)
    {
        Transform t = new GameObject("NeonVending").transform; t.SetParent(neonRoot, false);
        t.position = P(v.position); t.rotation = Quaternion.Euler(0, v.yaw, 0);
        Color body = v.variant == 0 ? Rgb(.05f, .18f, .5f) : Rgb(.5f, .06f, .18f);
        GameObject box = Prim(PrimitiveType.Cube, "Body", t, new Vector3(0, .93f, 0), new Vector3(1.0f, 1.86f, .78f), DarkMat("Vend" + v.variant, body), Quaternion.identity, true);
        Decor(box, false);
        GameObject front = CommonsWorldBuilder.Quad("VendFront", Vector3.zero, .92f, 1.68f, 0, SignMat(v.variant == 0 ? "neon_vending_a" : "neon_vending_b"));
        front.transform.SetParent(t, false); front.transform.localPosition = new Vector3(0, .95f, .395f); front.transform.localRotation = Quaternion.Euler(0, 180, 0); Decor(front, false);
        NeonPrim(PrimitiveType.Cube, "TopGlow", t, new Vector3(0, 1.9f, .2f), new Vector3(1.0f, .06f, .4f), NeonMat("VendGlow" + v.variant, v.variant == 0 ? Rgb(.3f, .7f, 1f) : Rgb(1f, .3f, .6f), 2.6f), Quaternion.identity, true);
    }
}
#endif
