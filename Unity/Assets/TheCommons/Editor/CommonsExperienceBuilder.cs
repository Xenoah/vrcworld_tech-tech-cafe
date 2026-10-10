#if UNITY_EDITOR
using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UdonSharp;
using UdonSharpEditor;
using VRC.SDK3.Components;

// Experience layer (v0.10.0-dev): view jack, adaptive music, sky deck, DATA
// STREAM ride, size lab and the KOMO companion. Called by CommonsWorldBuilder
// after lighting so every object lands in the same timestamped scene. All
// geometry here is generated from primitives and procedural meshes; the
// Blender model and its tcmesh records are not modified.
public static partial class CommonsExperienceBuilder
{
    const string Root = "Assets/TheCommons";
    const string AudioDir = Root + "/Audio/Experience/";
    static string Out;
    static bool Mobile;
    static List<Material> emissive;
    static List<Material> holos;
    static Dictionary<string, Material> baseMaterials;

    [Serializable] public class Layout { public string version; public Deck deck; public Lift lift; public float[] cafe_settings_panel; public float cafe_settings_yaw; public Ride ride; public Komo komo; }
    [Serializable] public class Deck { public float[] center, arrival, return_portal, return_destination, settings_panel, size_lab, planet, dock_exit, dock_board, dock_gate; public float floor_radius, field_radius, field_height, well_radius, planet_radius, arrival_yaw, return_portal_yaw, return_destination_yaw, settings_yaw, size_lab_yaw, dock_exit_yaw, board_yaw, dock_rail_x; }
    [Serializable] public class Lift { public float[] portal, destination; public float yaw, destination_yaw, frame_width; }
    [Serializable] public class Ride { public float[] points, speeds; public string[] cues; public Cue[] cue_map; public int samples_per_segment, cars; public float boarding, unload, roll_factor, roll_limit; }
    [Serializable] public class Cue { public string name; public int channel, sfx; public float seconds; }
    [Serializable] public class Komo { public Spot[] spots; public float[] hub; public int ride_every; public float travel_speed; }
    [Serializable] public class Spot { public string name; public int activity; public float[] position, door; public float yaw; }
    [Serializable] public class Score { public float bpm; public int bars, steps_per_bar; public float[] kick_soft, kick_dance, snare, hat, bass, bar_primary_rgb, bar_secondary_rgb; }

    public class Result
    {
        public CommonsViewJack viewJack;
        public CommonsAdaptiveMusic music;
        public bool adaptiveMusic;
        public GameObject viewJackOverlay;
        public List<Vector3> probes = new List<Vector3>();
    }

    static Vector3 P(float[] a) { return new Vector3(a[0], a[1], a[2]); }   // layout is already Unity X / Y up / Z

    public static Result Configure(string output, bool mobile, Dictionary<string, Material> materials, CommonsWorldState state,
        CommonsComfort comfort, CommonsLightingModes lighting, CommonsTimeOfDay time)
    {
        Out = output; Mobile = mobile; baseMaterials = materials;
        emissive = new List<Material>(); holos = new List<Material>();
        string path = Root + "/Data/experience_layout.json";
        if (!File.Exists(path)) throw new InvalidDataException("Missing experience_layout.json. Reimport the complete TheCommons folder.");
        Layout layout = JsonUtility.FromJson<Layout>(File.ReadAllText(path));
        if (layout == null || layout.deck == null || layout.ride == null || layout.komo == null || layout.lift == null)
            throw new InvalidDataException("Incomplete experience_layout.json.");
        foreach (string shader in new[] { "The Commons/Experience Toon", "The Commons/Holo Field", "The Commons/Komo Face", "The Commons/View Jack" })
            if (Shader.Find(shader) == null) throw new InvalidOperationException("Shader not compiled: " + shader + ". Check the Console for shader errors.");

        Result result = new Result();
        GameObject systems = new GameObject("INT_Experience"); systems.transform.SetParent(state.transform.parent);
        CommonsExperienceSettings settings = Add<CommonsExperienceSettings>(systems, "INT_ExperienceSettings");
        settings.comfort = comfort;
        CommonsAdaptiveMusic music = BuildMusic(systems, state, lighting, time, settings, result);
        CommonsViewJack jack = BuildViewJack(systems, settings, lighting, state, music, result);
        CommonsPlayerMotion motion = Add<CommonsPlayerMotion>(systems, "INT_PlayerMotion");
        motion.viewJack = jack; motion.music = music;
        motion.deckCenter = P(layout.deck.center); motion.deckRadius = layout.deck.floor_radius + 1f;
        CommonsRide ride = BuildRide(layout, jack, music, motion, settings, comfort);
        CommonsOrbitDeck deck = BuildDeck(layout, motion, jack, ride, music, comfort, settings, result);
        music.deck = deck;
        CommonsKomo komo = BuildKomo(layout, ride, music, settings, state, lighting, time, comfort);
        settings.music = music; settings.komo = komo;
        BuildCafeEntrances(layout, settings, jack, music, ride);
        BuildKartNeon();                                   // v0.11 Neo-Tokyo dressing for the kart hall

        // Every existing portal (floors, FPV, KART, returns) gains the optional warp.
        foreach (CommonsPortal portal in UnityEngine.Object.FindObjectsOfType<CommonsPortal>(true))
        {
            if (portal.viewJack == null) { portal.viewJack = jack; portal.music = music; }
            portal.ApplyProxyModifications();
        }
        // LOCAL COMFORT > LOW EMISSION also dims the experience materials.
        List<Material> luminous = new List<Material>(comfort.luminousMaterials ?? new Material[0]);
        luminous.AddRange(emissive); comfort.luminousMaterials = luminous.ToArray();
        deck.holoMaterials = holos.ToArray();

        settings.ApplyProxyModifications(); music.ApplyProxyModifications(); jack.ApplyProxyModifications();
        motion.ApplyProxyModifications(); ride.ApplyProxyModifications(); deck.ApplyProxyModifications();
        komo.ApplyProxyModifications(); comfort.ApplyProxyModifications();
        result.viewJack = jack; result.music = music;
        Debug.Log("THE COMMONS experience: ride " + ride.rideSeconds.ToString("0.0") + " s, cycle " + ride.CycleSeconds().ToString("0.0") + " s, adaptive music " + (result.adaptiveMusic ? "ON" : "missing stems, legacy loops kept"));
        return result;
    }

    // ------------------------------------------------------------ helpers
    static T Add<T>(GameObject parent, string name) where T : UdonSharpBehaviour
    {
        GameObject o = new GameObject(name); o.transform.SetParent(parent.transform, false);
        return o.AddUdonSharpComponent<T>();
    }
    static void Save(UnityEngine.Object asset, string folder, string extension)
    {
        CommonsWorldBuilder.SaveAsset(asset, Out + "/" + folder + "/" + asset.name + extension);
    }
    static Material Toon(string name, Color color, Color emission, float rim = .25f)
    {
        Material m = new Material(Shader.Find("The Commons/Experience Toon")); m.name = "EXP_" + name; m.enableInstancing = true;
        m.SetColor("_Color", color); m.SetColor("_EmissionColor", emission); m.SetFloat("_Rim", rim);
        Save(m, "Materials", ".mat");
        if (emission.maxColorComponent > 0f) emissive.Add(m);
        return m;
    }
    static Material Holo(string name, Color color, float intensity, Vector2 grid, float fadeTop, float scroll, float line = .06f)
    {
        Material m = new Material(Shader.Find("The Commons/Holo Field")); m.name = "EXP_" + name; m.enableInstancing = true;
        m.SetColor("_Color", color); m.SetFloat("_Intensity", intensity); m.SetVector("_Grid", new Vector4(grid.x, grid.y, 0, 0));
        m.SetFloat("_FadeTop", fadeTop); m.SetFloat("_Scroll", scroll); m.SetFloat("_Line", line); m.SetFloat("_Motion", 0f);
        Save(m, "Materials", ".mat"); holos.Add(m); emissive.Add(m);
        return m;
    }
    static GameObject Prim(PrimitiveType type, string name, Transform parent, Vector3 localPosition, Vector3 scale, Material material, Quaternion rotation, bool keepCollider = false)
    {
        GameObject o = GameObject.CreatePrimitive(type); o.name = name;
        if (!keepCollider) UnityEngine.Object.DestroyImmediate(o.GetComponent<Collider>());
        o.transform.SetParent(parent, false); o.transform.localPosition = localPosition; o.transform.localRotation = rotation; o.transform.localScale = scale;
        Renderer r = o.GetComponent<Renderer>(); r.sharedMaterial = material;
        r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        return o;
    }
    static GameObject MeshObject(string name, Transform parent, Mesh mesh, Material material, Vector3 position, Quaternion rotation)
    {
        GameObject o = new GameObject(name); o.transform.SetParent(parent, false); o.transform.position = position; o.transform.rotation = rotation;
        o.AddComponent<MeshFilter>().sharedMesh = mesh;
        MeshRenderer r = o.AddComponent<MeshRenderer>(); r.sharedMaterial = material; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        return o;
    }
    static void MarkStatic(GameObject o) { GameObjectUtility.SetStaticEditorFlags(o, StaticEditorFlags.BatchingStatic); }
    static Mesh Annulus(string name, float inner, float outer, int segments)
    {
        Mesh m = new Mesh(); m.name = "EXP_" + name;
        Vector3[] v = new Vector3[(segments + 1) * 2]; Vector2[] uv = new Vector2[v.Length]; int[] tri = new int[segments * 6];
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments; Vector3 d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            v[i * 2] = d * inner; v[i * 2 + 1] = d * outer;
            uv[i * 2] = new Vector2(i / (float)segments, 0); uv[i * 2 + 1] = new Vector2(i / (float)segments, 1);
            if (i < segments) { int k = i * 6, b = i * 2; tri[k] = b; tri[k + 1] = b + 2; tri[k + 2] = b + 1; tri[k + 3] = b + 1; tri[k + 4] = b + 2; tri[k + 5] = b + 3; }
        }
        m.vertices = v; m.uv = uv; m.triangles = tri; m.RecalculateNormals(); m.RecalculateBounds();
        Save(m, "Meshes", ".asset"); return m;
    }
    static Mesh Wall(string name, float radius, float height, int segments)
    {
        Mesh m = new Mesh(); m.name = "EXP_" + name;
        Vector3[] v = new Vector3[(segments + 1) * 2]; Vector3[] n = new Vector3[v.Length]; Vector2[] uv = new Vector2[v.Length]; int[] tri = new int[segments * 6];
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments; Vector3 d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            v[i * 2] = d * radius; v[i * 2 + 1] = d * radius + Vector3.up * height; n[i * 2] = d; n[i * 2 + 1] = d;
            uv[i * 2] = new Vector2(i / (float)segments, 0); uv[i * 2 + 1] = new Vector2(i / (float)segments, 1);
            if (i < segments) { int k = i * 6, b = i * 2; tri[k] = b; tri[k + 1] = b + 1; tri[k + 2] = b + 2; tri[k + 3] = b + 1; tri[k + 4] = b + 3; tri[k + 5] = b + 2; }
        }
        m.vertices = v; m.normals = n; m.uv = uv; m.triangles = tri; m.RecalculateBounds();
        Save(m, "Meshes", ".asset"); return m;
    }
    static Mesh Torus(string name, float major, float minor, int segments, int sides)
    {
        Mesh m = new Mesh(); m.name = "EXP_" + name;
        Vector3[] v = new Vector3[(segments + 1) * (sides + 1)]; Vector3[] n = new Vector3[v.Length]; Vector2[] uv = new Vector2[v.Length];
        int[] tri = new int[segments * sides * 6]; int t = 0;
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments; Vector3 c = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            for (int j = 0; j <= sides; j++)
            {
                float b = j * Mathf.PI * 2f / sides; Vector3 normal = c * Mathf.Cos(b) + Vector3.up * Mathf.Sin(b);
                int k = i * (sides + 1) + j; v[k] = c * major + normal * minor; n[k] = normal; uv[k] = new Vector2(i / (float)segments, j / (float)sides);
                if (i < segments && j < sides)
                {
                    int k2 = k + sides + 1;
                    tri[t++] = k; tri[t++] = k + 1; tri[t++] = k2; tri[t++] = k + 1; tri[t++] = k2 + 1; tri[t++] = k2;
                }
            }
        }
        m.vertices = v; m.normals = n; m.uv = uv; m.triangles = tri; m.RecalculateBounds();
        Save(m, "Meshes", ".asset"); return m;
    }
    static TextMesh Text(string name, string content, Vector3 position, float size, float yaw, Transform parent, Color color)
    {
        TextMesh t = CommonsWorldBuilder.Label(name, content, position, size, yaw);
        t.color = color; if (parent != null) t.transform.SetParent(parent, true);
        return t;
    }
    static Transform Marker(string name, Transform parent, Vector3 position, float yaw)
    {
        Transform t = new GameObject(name).transform; t.SetParent(parent, false); t.position = position; t.rotation = Quaternion.Euler(0, yaw, 0); return t;
    }
    static void Frame(Transform parent, Vector3 baseCenter, float width, float height, float yaw, Material material)
    {
        Quaternion r = Quaternion.Euler(0, yaw, 0);
        foreach (float side in new[] { -1f, 1f })
            Prim(PrimitiveType.Cube, "FramePost", parent, Vector3.zero, new Vector3(.12f, height, .16f), material, r).transform.position = baseCenter + r * new Vector3(side * width / 2f, height / 2f, 0);
        Prim(PrimitiveType.Cube, "FrameTop", parent, Vector3.zero, new Vector3(width + .12f, .12f, .16f), material, r).transform.position = baseCenter + Vector3.up * height;
    }

    // -------------------------------------------------------------- music
    static CommonsAdaptiveMusic BuildMusic(GameObject systems, CommonsWorldState state, CommonsLightingModes lighting, CommonsTimeOfDay time, CommonsExperienceSettings settings, Result result)
    {
        CommonsAdaptiveMusic music = Add<CommonsAdaptiveMusic>(systems, "INT_AdaptiveMusic");
        string[] stems = { "stem_0_pad", "stem_1_keys", "stem_2_bass", "stem_3_beat_soft", "stem_4_beat_dance", "stem_5_arp", "stem_6_sparkle" };
        string[] effects = { "sfx_0_whoosh", "sfx_1_glitch", "sfx_2_chime", "sfx_3_grow", "sfx_4_shrink", "sfx_5_click", "sfx_6_lift" };
        AudioSource[] sources = new AudioSource[stems.Length]; bool complete = true;
        for (int i = 0; i < stems.Length; i++)
        {
            AudioClip clip = AssetDatabase.LoadAssetAtPath<AudioClip>(AudioDir + stems[i] + ".ogg");
            if (clip == null) { complete = false; Debug.LogWarning("THE COMMONS: missing music stem " + stems[i]); }
            GameObject o = new GameObject("AUD_Stem_" + stems[i].Substring(7)); o.transform.SetParent(music.transform, false);
            AudioSource a = o.AddComponent<AudioSource>(); a.clip = clip; a.loop = true; a.playOnAwake = clip != null; a.volume = 0f;
            a.spatialBlend = 0f; a.priority = 40; a.dopplerLevel = 0f; sources[i] = a;
        }
        AudioClip[] clips = new AudioClip[effects.Length];
        for (int i = 0; i < effects.Length; i++) clips[i] = AssetDatabase.LoadAssetAtPath<AudioClip>(AudioDir + effects[i] + ".ogg");
        GameObject sfx = new GameObject("AUD_ExperienceSfx"); sfx.transform.SetParent(music.transform, false);
        AudioSource s2d = sfx.AddComponent<AudioSource>(); s2d.playOnAwake = false; s2d.spatialBlend = 0f; s2d.priority = 60;
        music.stems = sources; music.sfx = clips; music.sfxSource = s2d;
        music.state = state; music.lighting = lighting; music.timeOfDay = time; music.settings = settings;
        // v0.11: per-16th score of the generated stems drives music-synchronous lighting.
        string scorePath = Root + "/Data/music_score.json";
        if (File.Exists(scorePath))
        {
            Score score = JsonUtility.FromJson<Score>(File.ReadAllText(scorePath));
            music.bpm = score.bpm; music.bars = score.bars; music.stepsPerBar = score.steps_per_bar;
            music.scoreKickSoft = score.kick_soft; music.scoreKickDance = score.kick_dance; music.scoreSnare = score.snare;
            music.scoreHat = score.hat; music.scoreBass = score.bass;
            music.barPrimary = Colors(score.bar_primary_rgb); music.barSecondary = Colors(score.bar_secondary_rgb);
        }
        else Debug.LogWarning("THE COMMONS: music_score.json missing; lasers follow the server clock only.");
        lighting.music = music; lighting.ApplyProxyModifications();
        result.adaptiveMusic = complete;
        return music;
    }

    static Color[] Colors(float[] rgb)
    {
        if (rgb == null) return new Color[0];
        Color[] c = new Color[rgb.Length / 3];
        for (int i = 0; i < c.Length; i++) c[i] = new Color(rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2], 1f);
        return c;
    }

    // ----------------------------------------------------------- view jack
    static CommonsViewJack BuildViewJack(GameObject systems, CommonsExperienceSettings settings, CommonsLightingModes lighting, CommonsWorldState state, CommonsAdaptiveMusic music, Result result)
    {
        GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere); sphere.name = "EXP_ViewJackOverlay";
        UnityEngine.Object.DestroyImmediate(sphere.GetComponent<Collider>());
        sphere.transform.SetParent(systems.transform, false); sphere.transform.localScale = Vector3.one * 1.6f;
        Material m = new Material(Shader.Find("The Commons/View Jack")); m.name = "EXP_ViewJack"; Save(m, "Materials", ".mat");
        Renderer r = sphere.GetComponent<Renderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        r.allowOcclusionWhenDynamic = false; r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off; r.enabled = false;
        CommonsViewJack jack = Add<CommonsViewJack>(systems, "INT_ViewJack");
        jack.overlay = r; jack.material = m; jack.settings = settings; jack.lighting = lighting; jack.state = state; jack.music = music;
        result.viewJackOverlay = sphere;
        return jack;
    }

    // ---------------------------------------------------------------- ride
    static float Knot(Vector3 a, Vector3 b) { return Mathf.Max(Mathf.Sqrt(Vector3.Distance(a, b)), 1e-4f); }
    // Closed centripetal Catmull-Rom; mirrors Blender/build_experience_layout.py.
    static Vector3 Centripetal(Vector3[] p, float t)
    {
        int n = p.Length; int i = Mathf.FloorToInt(t); float u = t - i; i = ((i % n) + n) % n;
        Vector3 p0 = p[(i - 1 + n) % n], p1 = p[i], p2 = p[(i + 1) % n], p3 = p[(i + 2) % n];
        float t0 = 0f, t1 = t0 + Knot(p0, p1), t2 = t1 + Knot(p1, p2), t3 = t2 + Knot(p2, p3), tt = t1 + (t2 - t1) * u;
        Vector3 a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1;
        Vector3 a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2;
        Vector3 a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3;
        Vector3 b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2;
        Vector3 b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3;
        return (t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2;
    }
    static float SpeedAt(float[] s, float t)
    {
        int n = s.Length; int i = Mathf.FloorToInt(t); float u = t - i; i = ((i % n) + n) % n; u = u * u * (3f - 2f * u);
        return s[i] * (1f - u) + s[(i + 1) % n] * u;
    }
    public static void Bake(CommonsRide ride, Vector3[] control, float[] speeds, int perSegment, float rollFactor, float rollLimit)
    {
        int n = control.Length, count = n * perSegment + 1;
        Vector3[] pos = new Vector3[count]; Vector3[] tan = new Vector3[count];
        float[] v = new float[count], time = new float[count], roll = new float[count]; int[] segment = new int[count];
        for (int k = 0; k < count; k++)
        {
            float t = k / (float)perSegment; pos[k] = Centripetal(control, t); v[k] = Mathf.Max(.3f, SpeedAt(speeds, t)); segment[k] = Mathf.Min(n - 1, k / perSegment);
            if (k > 0) time[k] = time[k - 1] + Vector3.Distance(pos[k - 1], pos[k]) / Mathf.Max(.3f, (v[k - 1] + v[k]) * .5f);
        }
        for (int k = 0; k < count; k++)
        {
            Vector3 a = pos[k == 0 ? count - 2 : k - 1], b = pos[k == count - 1 ? 1 : k + 1];
            tan[k] = (b - a).normalized;
        }
        float[] raw = new float[count];
        for (int k = 0; k < count; k++)
        {
            int ka = k == 0 ? count - 2 : k - 1, kb = k == count - 1 ? 1 : k + 1;
            float ds = Mathf.Max(.01f, Vector3.Distance(pos[ka], pos[kb]));
            Vector3 curvature = (tan[kb] - tan[ka]) / ds;
            Vector3 right = Vector3.Cross(Vector3.up, tan[k]).normalized;
            float lateral = v[k] * v[k] * Vector3.Dot(curvature, right);
            raw[k] = Mathf.Clamp(-Mathf.Atan(lateral / 9.81f) * Mathf.Rad2Deg * rollFactor, -rollLimit, rollLimit);
        }
        for (int k = 0; k < count; k++)
        {
            float sum = 0f; int w = 0;
            for (int d = -8; d <= 8; d++) { int j = k + d; if (j < 0) j += count - 1; if (j >= count) j -= count - 1; sum += raw[j]; w++; }
            roll[k] = sum / w;
        }
        ride.samplePositions = pos; ride.sampleTangents = tan; ride.sampleSpeeds = v; ride.sampleTimes = time;
        ride.sampleRoll = roll; ride.sampleSegments = segment; ride.rideSeconds = time[count - 1];
    }
    static CommonsRide BuildRide(Layout layout, CommonsViewJack jack, CommonsAdaptiveMusic music, CommonsPlayerMotion motion, CommonsExperienceSettings settings, CommonsComfort comfort)
    {
        Ride R = layout.ride; Deck D = layout.deck;
        GameObject root = new GameObject("ATTR_DataStream");
        CommonsRide ride = root.AddUdonSharpComponent<CommonsRide>();
        int n = R.speeds.Length; Vector3[] control = new Vector3[n];
        Transform pathRoot = new GameObject("Path_ControlPoints (edit, then The Commons/Experience/Rebake Ride)").transform; pathRoot.SetParent(root.transform, false);
        for (int i = 0; i < n; i++)
        {
            control[i] = new Vector3(R.points[i * 3], R.points[i * 3 + 1], R.points[i * 3 + 2]);
            Marker("CP_" + i.ToString("000") + (string.IsNullOrEmpty(R.cues[i]) ? "" : "_" + R.cues[i]), pathRoot, control[i], 0);
        }
        Bake(ride, control, R.speeds, R.samples_per_segment, R.roll_factor, R.roll_limit);
        int[] effects = new int[n]; float[] seconds = new float[n]; int[] sfx = new int[n];
        for (int i = 0; i < n; i++)
        {
            effects[i] = -1; sfx[i] = -1;
            foreach (Cue c in R.cue_map) if (c.name == R.cues[i]) { effects[i] = c.channel; seconds[i] = c.seconds; sfx[i] = c.sfx; }
        }
        ride.cueEffects = effects; ride.cueSeconds = seconds; ride.cueSfx = sfx;
        ride.boardingSeconds = R.boarding; ride.unloadSeconds = R.unload;
        ride.deckCenter = P(D.center); ride.deckFieldRadius = D.field_radius;
        Material body = Toon("RideBody", new Color(.88f, .9f, .94f), Color.black, .35f);
        Material seat = Toon("RideSeat", new Color(.08f, .09f, .12f), Color.black, .1f);
        Material accent = Toon("RideAccent", new Color(.4f, .25f, .9f), new Color(.35f, .18f, .9f) * .9f, .4f);
        Material strip = Toon("RideStrip", new Color(.05f, .5f, .7f), new Color(.05f, .75f, 1f) * 1.2f, .2f);
        Material steel = baseMaterials.ContainsKey("MAT_Steel") ? baseMaterials["MAT_Steel"] : seat;
        AudioClip hum = AssetDatabase.LoadAssetAtPath<AudioClip>(AudioDir + "ride_hum_loop.ogg");
        int cars = Mathf.Max(1, R.cars);
        Transform[] carTransforms = new Transform[cars]; Transform[] mounts = new Transform[cars]; AudioSource[] audio = new AudioSource[cars];
        List<CommonsRideSeat> seats = new List<CommonsRideSeat>();
        for (int c = 0; c < cars; c++)
        {
            string letter = ((char)('A' + c)).ToString();
            Transform car = new GameObject("Car_" + letter).transform; car.SetParent(root.transform, false);
            car.SetPositionAndRotation(ride.samplePositions[0], Quaternion.LookRotation(ride.sampleTangents[0]));
            Rigidbody rb = car.gameObject.AddComponent<Rigidbody>(); rb.isKinematic = true; rb.useGravity = false;
            Prim(PrimitiveType.Cube, "Chassis", car, new Vector3(0, .16f, 0), new Vector3(1.9f, .32f, 3.3f), body, Quaternion.identity);
            Prim(PrimitiveType.Sphere, "Nose", car, new Vector3(0, .3f, 1.65f), new Vector3(1.9f, .55f, 1.3f), body, Quaternion.identity);
            Prim(PrimitiveType.Cube, "TailFin", car, new Vector3(0, .55f, -1.5f), new Vector3(.08f, .55f, .7f), accent, Quaternion.identity);
            foreach (float side in new[] { -1f, 1f })
                Prim(PrimitiveType.Cube, "LightStrip", car, new Vector3(side * .965f, .26f, 0), new Vector3(.03f, .06f, 3.0f), strip, Quaternion.identity);
            Text("RideCar_" + letter, letter, Vector3.zero, .2f, 0, car, new Color(.6f, .45f, 1f)).transform.localPosition = new Vector3(0, .55f, -1.86f);
            int index = 0;
            foreach (float z in new[] { .45f, -.75f })
            {
                Prim(PrimitiveType.Cube, "LapBar", car, new Vector3(0, .8f, z + .3f), new Vector3(1.5f, .05f, .05f), steel, Quaternion.identity);
                foreach (float x in new[] { -.45f, .45f })
                {
                    Prim(PrimitiveType.Cube, "Cushion", car, new Vector3(x, .38f, z), new Vector3(.52f, .12f, .5f), seat, Quaternion.identity);
                    Prim(PrimitiveType.Cube, "Back", car, new Vector3(x, .72f, z - .27f), new Vector3(.52f, .62f, .08f), seat, Quaternion.identity);
                    GameObject s = new GameObject("Seat_" + letter + (++index)); s.transform.SetParent(car, false); s.transform.localPosition = new Vector3(x, .45f, z);
                    BoxCollider hit = s.AddComponent<BoxCollider>(); hit.isTrigger = true; hit.size = new Vector3(.55f, .7f, .55f); hit.center = new Vector3(0, .3f, 0);
                    VRCStation st = s.AddComponent<VRCStation>(); st.PlayerMobility = VRC.SDKBase.VRCStation.Mobility.Immobilize; st.seated = true;
                    st.disableStationExit = false; st.canUseStationFromStation = false;
                    Transform enter = new GameObject("Enter").transform; enter.SetParent(s.transform, false);
                    Transform exit = new GameObject("Exit").transform; exit.SetParent(s.transform, false); exit.localPosition = new Vector3(0, .1f, 0);
                    st.stationEnterPlayerLocation = enter; st.stationExitPlayerLocation = exit;
                    CommonsRideSeat rs = s.AddUdonSharpComponent<CommonsRideSeat>(); rs.ride = ride; rs.station = st; rs.car = c; rs.ApplyProxyModifications();
                    CommonsWorldBuilder.InteractSettings(rs, "Board DATA STREAM", 2.5f); seats.Add(rs);
                }
            }
            mounts[c] = Marker("KomoMount", car, Vector3.zero, 0); mounts[c].localPosition = new Vector3(0, .82f, 1.95f); mounts[c].localRotation = Quaternion.identity;
            AudioSource a = car.gameObject.AddComponent<AudioSource>(); a.clip = hum; a.loop = true; a.playOnAwake = hum != null; a.volume = .08f;
            a.spatialBlend = 1f; a.minDistance = 2f; a.maxDistance = 50f; a.rolloffMode = AudioRolloffMode.Logarithmic; a.dopplerLevel = .5f; a.priority = 90;
            carTransforms[c] = car; audio[c] = a;
        }
        ride.cars = carTransforms; ride.komoMounts = mounts; ride.seats = seats.ToArray(); ride.carAudio = audio;
        ride.exitPoint = Marker("DockExit", root.transform, P(D.dock_exit), D.dock_exit_yaw);
        ride.boards = new[] { Text("RideBoard", "DATA STREAM", P(D.dock_board), .1f, D.board_yaw, root.transform, new Color(.75f, .9f, 1f)) };
        ride.viewJack = jack; ride.music = music; ride.motion = motion; ride.settings = settings; ride.comfort = comfort;
        float spacing = ride.CycleSeconds() / cars;
        if (spacing < ride.boardingSeconds + ride.unloadSeconds || ride.rideSeconds < spacing)
            Debug.LogWarning("THE COMMONS: ride timing lets two cars share the dock; adjust boarding/unload or car count.");
        return ride;
    }
    [MenuItem("The Commons/Experience/Rebake Ride (from Path control points)")]
    public static void RebakeRide()
    {
        CommonsRide ride = UnityEngine.Object.FindObjectOfType<CommonsRide>();
        if (ride == null) { Debug.LogWarning("No CommonsRide in the open scene."); return; }
        Transform path = null;
        foreach (Transform child in ride.transform) if (child.name.StartsWith("Path_ControlPoints")) path = child;
        Layout layout = JsonUtility.FromJson<Layout>(File.ReadAllText(Root + "/Data/experience_layout.json"));
        if (path == null || layout == null || path.childCount != layout.ride.speeds.Length) { Debug.LogWarning("Path control points do not match experience_layout.json speeds."); return; }
        Vector3[] control = new Vector3[path.childCount];
        for (int i = 0; i < control.Length; i++) control[i] = path.GetChild(i).position;
        Undo.RecordObject(ride, "Rebake ride");
        Bake(ride, control, layout.ride.speeds, layout.ride.samples_per_segment, layout.ride.roll_factor, layout.ride.roll_limit);
        ride.ApplyProxyModifications(); EditorUtility.SetDirty(ride);
        Debug.Log("DATA STREAM rebaked: " + ride.rideSeconds.ToString("0.0") + " s. Save the scene.");
    }

    // ---------------------------------------------------------------- deck
    static CommonsOrbitDeck BuildDeck(Layout layout, CommonsPlayerMotion motion, CommonsViewJack jack, CommonsRide ride, CommonsAdaptiveMusic music, CommonsComfort comfort, CommonsExperienceSettings settings, Result result)
    {
        Deck D = layout.deck; Vector3 C = P(D.center); float R = D.floor_radius;
        GameObject root = new GameObject("ATTR_OrbitDeck");
        CommonsOrbitDeck deck = root.AddUdonSharpComponent<CommonsOrbitDeck>();
        Material floor = Toon("DeckFloor", new Color(.12f, .13f, .16f), Color.black, .1f);
        Material trim = Toon("DeckTrim", new Color(.72f, .75f, .8f), Color.black, .3f);
        Material core = Toon("DeckCore", new Color(.05f, .06f, .09f), new Color(.02f, .1f, .25f), .2f);
        Material ringCyan = Holo("DeckRingCyan", new Color(.05f, .75f, 1f), 1.1f, new Vector2(96, 1), 0, 0, .5f);
        Material ringViolet = Holo("DeckWell", new Color(.62f, .35f, 1f), 1.2f, new Vector2(72, 1), 0, 0, .5f);
        Material field = Holo("DeckField", new Color(.1f, .6f, 1f), .35f, new Vector2(96, 10), 1, .02f);
        Material lane = Holo("DeckLane", new Color(.05f, .75f, 1f), .7f, new Vector2(2, 30), 0, .4f);
        Material planetShell = Holo("Planet", new Color(.15f, .8f, 1f), .8f, new Vector2(24, 12), 0, .01f);
        Material planetCore = Toon("PlanetCore", new Color(.02f, .05f, .12f), new Color(.02f, .12f, .3f), .6f);
        Material amber = Holo("HaloAmber", new Color(1f, .6f, .25f), .9f, new Vector2(120, 1), 0, 0, .5f);
        Material glass = new Material(Shader.Find("The Commons/Smoked Glass")); glass.name = "EXP_DeckGlass"; glass.SetColor("_Color", new Color(.2f, .36f, .4f, .12f)); Save(glass, "Materials", ".mat");

        GameObject floorObj = Prim(PrimitiveType.Cylinder, "Deck_Floor", root.transform, Vector3.zero, new Vector3(R * 2f, .3f, R * 2f), floor, Quaternion.identity);
        floorObj.transform.position = C - new Vector3(0, .3f, 0);
        floorObj.AddComponent<MeshCollider>().sharedMesh = floorObj.GetComponent<MeshFilter>().sharedMesh; MarkStatic(floorObj);
        GameObject under = Prim(PrimitiveType.Cylinder, "Deck_Core", root.transform, Vector3.zero, new Vector3(R * 1.1f, 1.4f, R * 1.1f), core, Quaternion.identity);
        under.transform.position = C - new Vector3(0, 2f, 0); MarkStatic(under);
        foreach (GameObject ring in new[] {
            MeshObject("Deck_WellRing", root.transform, Annulus("WellRing", D.well_radius - .12f, D.well_radius + .12f, 96), ringViolet, C + Vector3.up * .012f, Quaternion.identity),
            MeshObject("Deck_MidRing", root.transform, Annulus("MidRing", 12f, 12.12f, 128), ringCyan, C + Vector3.up * .012f, Quaternion.identity),
            MeshObject("Deck_EdgeRing", root.transform, Annulus("EdgeRing", R - .35f, R - .15f, 160), ringCyan, C + Vector3.up * .012f, Quaternion.identity),
            MeshObject("Deck_Field", root.transform, Wall("Field", D.field_radius, 7f, 160), field, C, Quaternion.identity),
            MeshObject("Deck_Parapet", root.transform, Wall("Parapet", D.field_radius - .03f, 1.1f, 160), glass, C, Quaternion.identity),
            MeshObject("Deck_ParapetRail", root.transform, Torus("ParapetRail", D.field_radius - .03f, .03f, 160, 6), trim, C + Vector3.up * 1.1f, Quaternion.identity) })
            MarkStatic(ring);
        Text("WellLabel", "GRAVITY WELL\nhold JUMP to float", C + new Vector3(0, .03f, -D.well_radius - .9f), .16f, 0, root.transform, new Color(.8f, .65f, 1f)).transform.rotation = Quaternion.Euler(90, 0, 0);
        // Invisible field: a ring of walls and a lid, so nobody falls or thrusts away.
        Transform colliders = new GameObject("Deck_FieldColliders").transform; colliders.SetParent(root.transform, false);
        int walls = 40; float wallRadius = D.field_radius + .3f;
        for (int i = 0; i < walls; i++)
        {
            float a = (i + .5f) * Mathf.PI * 2f / walls;
            GameObject w = new GameObject("FieldWall_" + i); w.transform.SetParent(colliders, false);
            w.transform.position = C + new Vector3(Mathf.Cos(a) * wallRadius, D.field_height / 2f, Mathf.Sin(a) * wallRadius);
            w.transform.rotation = Quaternion.LookRotation(new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)));
            w.AddComponent<BoxCollider>().size = new Vector3(2f * Mathf.PI * wallRadius / walls + .4f, D.field_height, .6f); w.isStatic = true;
        }
        GameObject lid = new GameObject("FieldLid"); lid.transform.SetParent(colliders, false); lid.transform.position = C + Vector3.up * (D.field_height + .3f);
        lid.AddComponent<BoxCollider>().size = new Vector3(R * 2f + 4f, .6f, R * 2f + 4f); lid.isStatic = true;
        // Holo planet above the gravity well and two slow halo rings.
        Transform planet = new GameObject("Deck_Planet").transform; planet.SetParent(root.transform, false); planet.position = P(D.planet);
        float pr = D.planet_radius;
        Prim(PrimitiveType.Sphere, "Core", planet, Vector3.zero, Vector3.one * pr * 1.84f, planetCore, Quaternion.identity);
        Prim(PrimitiveType.Sphere, "Shell", planet, Vector3.zero, Vector3.one * pr * 2f, planetShell, Quaternion.identity);
        MeshObject("Ring", planet, Torus("PlanetRing", pr * 1.6f, .05f, 96, 6), ringViolet, planet.position, Quaternion.Euler(20, 0, 8));
        List<Transform> spinners = new List<Transform>();
        if (!Mobile)
        {
            spinners.Add(MeshObject("Deck_Halo_A", root.transform, Torus("HaloA", 14f, .06f, 160, 6), ringCyan, C + Vector3.up * 9f, Quaternion.identity).transform);
            spinners.Add(MeshObject("Deck_Halo_B", root.transform, Torus("HaloB", 15.5f, .05f, 160, 6), amber, C + Vector3.up * 10.5f, Quaternion.Euler(6, 0, 0)).transform);
        }
        // Dock lane and rails. The car rides through, players board from the west side gate.
        float laneZ0 = -6f, laneZ1 = 13.5f;
        GameObject laneObj = Prim(PrimitiveType.Quad, "Deck_DockLane", root.transform, Vector3.zero, new Vector3(1.9f, laneZ1 - laneZ0, 1f), lane, Quaternion.Euler(90, 0, 0));
        laneObj.transform.position = new Vector3(26f, C.y + .011f, (laneZ0 + laneZ1) / 2f); MarkStatic(laneObj);
        float railX = D.dock_rail_x;
        foreach (Vector2 span in new[] { new Vector2(-4f, D.dock_gate[0]), new Vector2(D.dock_gate[1], laneZ1) })
            Rail(root.transform, new Vector3(railX, C.y, span.x), new Vector3(railX, C.y, span.y), trim);
        Rail(root.transform, new Vector3(27.6f, C.y, laneZ0), new Vector3(27.6f, C.y, laneZ1), trim);
        Text("DockSign", "DATA STREAM\nboard here", new Vector3(railX - .05f, C.y + 2.35f, (D.dock_gate[0] + D.dock_gate[1]) / 2f), .16f, 90, root.transform, new Color(.6f, .9f, 1f));
        // Arrival pad, sign and return portal.
        Vector3 arrival = P(D.arrival);
        MeshObject("Deck_ArrivalPad", root.transform, Annulus("ArrivalPad", .02f, 1.0f, 48), ringViolet, arrival + Vector3.up * .013f, Quaternion.identity);
        Text("DeckTitle", "ORBIT DECK", arrival + new Vector3(0, 3.6f, 6.5f), .42f, 0, root.transform, new Color(.85f, .8f, 1f));
        Text("DeckSubtitle", "GRAVITY WELL  /  DATA STREAM  /  SIZE LAB", arrival + new Vector3(0, 3.05f, 6.5f), .12f, 0, root.transform, new Color(.7f, .85f, 1f));
        Transform back = Marker("TP_ReturnToCafe", root.transform, P(D.return_destination), D.return_destination_yaw);
        PortalPanel("RETURN TO CAFE", P(D.return_portal), D.return_portal_yaw, back, jack, music, 0, new Color(.06f, .04f, .02f), accent: ringViolet, parent: root.transform);
        // Size lab and a second EXPERIENCE panel.
        Vector3 lab = P(D.size_lab); float labYaw = D.size_lab_yaw; Quaternion lr = Quaternion.Euler(0, labYaw, 0);
        MeshObject("SizeLab_Pad", root.transform, Annulus("SizeLabPad", 1.0f, 1.25f, 64), amber, new Vector3(lab.x, C.y + .013f, lab.z) + lr * new Vector3(0, 0, -1.8f), Quaternion.identity);
        motion.labels = new[] { Text("SizeLab", "SIZE LAB (LOCAL)", lab + lr * new Vector3(0, .72f, -.05f), .085f, labYaw, root.transform, new Color(1f, .85f, .6f)) };
        string[] sizeTitles = { "TINY x0.1", "SMALL x0.5", "NORMAL", "GIANT x4" }, sizeEvents = { "Tiny", "Small", "Normal", "Giant" };
        for (int i = 0; i < 4; i++) CommonsWorldBuilder.Button(sizeTitles[i], lab + lr * new Vector3((i % 2 - .5f) * 1.04f, .2f - (i / 2) * .32f, 0), motion, sizeEvents[i], .98f, .27f, labYaw);
        SettingsPanel(P(D.settings_panel), D.settings_yaw, settings, root.transform);
        // Deck behaviour.
        deck.motion = motion; deck.viewJack = jack; deck.ride = ride; deck.music = music; deck.comfort = comfort;
        deck.arrival = Marker("DeckArrival", root.transform, arrival, D.arrival_yaw);
        deck.planet = planet; deck.spinners = spinners.ToArray();
        deck.center = C; deck.radius = D.field_radius; deck.wellRadius = D.well_radius; deck.ceiling = D.field_height;
        motion.wellGravity = .16f;
        foreach (float r in new[] { 2f, 8f, 14f })
            for (int i = 0; i < 8; i++)
            {
                float a = i * Mathf.PI / 4f;
                foreach (float y in new[] { 1.2f, 5f }) result.probes.Add(C + new Vector3(Mathf.Cos(a) * r, y, Mathf.Sin(a) * r));
            }
        result.probes.Add(C + Vector3.up * 12f);
        return deck;
    }
    static void Rail(Transform parent, Vector3 from, Vector3 to, Material material)
    {
        Vector3 mid = (from + to) / 2f; float length = Vector3.Distance(from, to);
        GameObject top = Prim(PrimitiveType.Cube, "Rail", parent, Vector3.zero, new Vector3(.06f, .06f, length), material, Quaternion.LookRotation(to - from));
        top.transform.position = mid + Vector3.up * 1.0f; MarkStatic(top);
        GameObject block = new GameObject("RailCollider"); block.transform.SetParent(parent, false); block.transform.position = mid + Vector3.up * .55f; block.transform.rotation = Quaternion.LookRotation(to - from);
        block.AddComponent<BoxCollider>().size = new Vector3(.12f, 1.1f, length); block.isStatic = true;
        for (float d = 0; d <= length + .01f; d += 2f)
        {
            GameObject post = Prim(PrimitiveType.Cube, "RailPost", parent, Vector3.zero, new Vector3(.05f, 1f, .05f), material, Quaternion.identity);
            post.transform.position = Vector3.Lerp(from, to, d / Mathf.Max(.01f, length)) + Vector3.up * .5f; MarkStatic(post);
        }
    }
    static CommonsPortal PortalPanel(string title, Vector3 position, float yaw, Transform destination, CommonsViewJack jack, CommonsAdaptiveMusic music, int sfx, Color warpColor, Material accent, Transform parent)
    {
        Quaternion r = Quaternion.Euler(0, yaw, 0);
        GameObject o = GameObject.CreatePrimitive(PrimitiveType.Cube); o.name = "INT_Portal_" + title; o.transform.SetParent(parent, false);
        o.transform.position = position; o.transform.rotation = r; o.transform.localScale = new Vector3(2.1f, .72f, .12f);
        o.GetComponent<Renderer>().sharedMaterial = baseMaterials.ContainsKey("MAT_Black") ? baseMaterials["MAT_Black"] : accent;
        Text("Portal_" + title, title, position + r * new Vector3(0, 0, -.072f), .11f, yaw, parent, new Color(.9f, .92f, 1f));
        Frame(parent, new Vector3(position.x, position.y - 1.3f, position.z) + r * new Vector3(0, 0, .05f), 2.4f, 2.9f, yaw, accent);
        CommonsPortal portal = o.AddUdonSharpComponent<CommonsPortal>(); portal.destination = destination;
        portal.viewJack = jack; portal.music = music; portal.sfx = sfx; portal.warpColor = warpColor; portal.ApplyProxyModifications();
        CommonsWorldBuilder.InteractSettings(portal, title, 2.5f);
        return portal;
    }
    static void SettingsPanel(Vector3 p, float yaw, CommonsExperienceSettings settings, Transform parent)
    {
        Quaternion r = Quaternion.Euler(0, yaw, 0);
        TextMesh label = Text("Experience", "EXPERIENCE (LOCAL)", p + r * new Vector3(0, .78f, -.05f), .062f, yaw, parent, new Color(.85f, .9f, 1f));
        List<TextMesh> labels = new List<TextMesh>(); if (settings.labels != null) labels.AddRange(settings.labels); labels.Add(label); settings.labels = labels.ToArray();
        string[] titles = { "VIEW FX OFF/SOFT/FULL", "WARP ON / OFF", "RIDE FX ON / OFF", "AMBIENT FX", "BEAT PULSE", "RIDE VIGNETTE", "MUSIC -", "MUSIC +", "KOMO TALK / QUIET", "KOMO EN / JP" };
        string[] events = { "CycleViewFx", "ToggleTransitions", "ToggleAttractions", "ToggleAmbient", "ToggleBeatPulse", "ToggleComfortVignette", "MusicDown", "MusicUp", "ToggleKomoBubbles", "ToggleKomoLanguage" };
        for (int i = 0; i < titles.Length; i++)
            CommonsWorldBuilder.Button(titles[i], p + r * new Vector3((i % 2 - .5f) * 1.04f, .3f - (i / 2) * .3f, 0), settings, events[i], .98f, .25f, yaw);
    }

    // ------------------------------------------------------- cafe entries
    static void BuildCafeEntrances(Layout layout, CommonsExperienceSettings settings, CommonsViewJack jack, CommonsAdaptiveMusic music, CommonsRide ride)
    {
        Lift L = layout.lift; Vector3 p = P(L.portal); Quaternion r = Quaternion.Euler(0, L.yaw, 0);
        GameObject root = new GameObject("WAY_ORBIT_Cafe");
        Material violet = Toon("LiftFrame", new Color(.45f, .3f, .95f), new Color(.45f, .25f, 1f) * 1.1f, .4f);
        Material pad = Holo("LiftPad", new Color(.62f, .35f, 1f), 1.1f, new Vector2(48, 1), 0, 0, .5f);
        Transform destination = Marker("TP_ORBIT", root.transform, P(L.destination), L.destination_yaw);
        GameObject o = GameObject.CreatePrimitive(PrimitiveType.Cube); o.name = "INT_Portal_ORBIT"; o.transform.SetParent(root.transform, false);
        o.transform.position = p; o.transform.rotation = r; o.transform.localScale = new Vector3(1.9f, .72f, .12f);
        o.GetComponent<Renderer>().sharedMaterial = baseMaterials.ContainsKey("MAT_Black") ? baseMaterials["MAT_Black"] : violet;
        Text("Lift_GO", "GO TO ORBIT", p + r * new Vector3(0, 0, -.072f), .1f, L.yaw, root.transform, new Color(.92f, .9f, 1f));
        Text("Lift_Title", "ORBIT", p + r * new Vector3(0, 1.05f, -.08f), .3f, L.yaw, root.transform, new Color(.78f, .62f, 1f));
        Text("Lift_Sub", "SKY DECK / DATA STREAM / SIZE LAB", p + r * new Vector3(0, .72f, -.08f), .07f, L.yaw, root.transform, new Color(.8f, .85f, 1f));
        Frame(root.transform, new Vector3(p.x, 0, p.z) + r * new Vector3(0, 0, .06f), L.frame_width, 2.9f, L.yaw, violet);
        MeshObject("Lift_FloorPad", root.transform, Annulus("LiftFloorPad", .6f, .85f, 48), pad, new Vector3(p.x, .02f, p.z) + r * new Vector3(0, 0, -1.2f), Quaternion.identity);
        CommonsPortal portal = o.AddUdonSharpComponent<CommonsPortal>(); portal.destination = destination; portal.viewJack = jack; portal.music = music;
        portal.sfx = 6; portal.warpColor = new Color(.05f, .02f, .1f); portal.ApplyProxyModifications();
        CommonsWorldBuilder.InteractSettings(portal, "GO TO ORBIT DECK", 2.5f);
        List<TextMesh> boards = new List<TextMesh>(ride.boards);
        boards.Add(Text("Lift_RideBoard", "DATA STREAM", p + r * new Vector3(0, 1.85f, -.08f), .05f, L.yaw, root.transform, new Color(.7f, .85f, 1f)));
        ride.boards = boards.ToArray();
        SettingsPanel(P(layout.cafe_settings_panel), layout.cafe_settings_yaw, settings, root.transform);
    }

    // ---------------------------------------------------------------- KOMO
    static CommonsKomo BuildKomo(Layout layout, CommonsRide ride, CommonsAdaptiveMusic music, CommonsExperienceSettings settings, CommonsWorldState state, CommonsLightingModes lighting, CommonsTimeOfDay time, CommonsComfort comfort)
    {
        Komo K = layout.komo;
        GameObject root = new GameObject("NPC_KOMO"); root.transform.position = P(K.spots[0].position);
        Rigidbody rb = root.AddComponent<Rigidbody>(); rb.isKinematic = true; rb.useGravity = false;
        SphereCollider hit = root.AddComponent<SphereCollider>(); hit.radius = .38f; hit.isTrigger = true;
        CommonsKomo komo = root.AddUdonSharpComponent<CommonsKomo>();
        Material shell = Toon("KomoShell", new Color(.95f, .94f, .9f), Color.black, .35f);
        Material dark = Toon("KomoDark", new Color(.1f, .11f, .14f), Color.black, .15f);
        Material tip = Toon("KomoTip", new Color(1f, .62f, .25f), new Color(1f, .5f, .15f) * 1.2f, .2f);
        Material ceramic = Toon("KomoCup", new Color(.96f, .96f, .94f), Color.black, .2f);
        Material coffee = Toon("KomoCoffee", new Color(.25f, .14f, .07f), Color.black, .05f);
        Material cover = Toon("KomoBook", new Color(.1f, .45f, .5f), Color.black, .2f);
        Material ringMat = Holo("KomoRing", new Color(.1f, .8f, 1f), 1.2f, new Vector2(48, 1), 0, 0, .5f);
        Material face = new Material(Shader.Find("The Commons/Komo Face")); face.name = "EXP_KomoFace"; Save(face, "Materials", ".mat"); emissive.Add(face);
        Material glow = new Material(Shader.Find("The Commons/Soft Fixture Glow")); glow.name = "EXP_KomoGlow"; glow.SetColor("_Color", new Color(.1f, .7f, 1f)); glow.SetFloat("_Intensity", .12f); Save(glow, "Materials", ".mat"); emissive.Add(glow);
        Material bubbleBack = Toon("KomoBubble", new Color(.03f, .05f, .09f), new Color(.015f, .03f, .06f), 0f);

        Transform body = new GameObject("Body").transform; body.SetParent(root.transform, false);
        Prim(PrimitiveType.Sphere, "Shell", body, Vector3.zero, new Vector3(.46f, .42f, .42f), shell, Quaternion.identity);
        // The shell radius is .21 m: keep the screen just outside it so the shell never hides the face.
        Prim(PrimitiveType.Quad, "Face", body, new Vector3(0, .02f, .215f), new Vector3(.34f, .25f, 1f), face, Quaternion.Euler(0, 180, 0));
        foreach (float side in new[] { -1f, 1f })
        {
            Prim(PrimitiveType.Cylinder, "Antenna", body, new Vector3(side * .11f, .25f, -.02f), new Vector3(.02f, .06f, .02f), dark, Quaternion.Euler(0, 0, -side * 15f));
            Prim(PrimitiveType.Sphere, "AntennaTip", body, new Vector3(side * .13f, .32f, -.02f), Vector3.one * .055f, tip, Quaternion.identity);
        }
        Transform handL = Prim(PrimitiveType.Sphere, "HandL", body, new Vector3(-.3f, -.05f, .1f), Vector3.one * .1f, shell, Quaternion.identity).transform;
        Transform handR = Prim(PrimitiveType.Sphere, "HandR", body, new Vector3(.3f, -.05f, .1f), Vector3.one * .1f, shell, Quaternion.identity).transform;
        Transform ring = MeshObject("OrbitRing", body, Torus("KomoRing", .34f, .016f, 64, 6), ringMat, root.transform.position, Quaternion.Euler(14, 0, 8)).transform;
        Prim(PrimitiveType.Quad, "ThrusterGlow", body, new Vector3(0, -.33f, 0), Vector3.one * .55f, glow, Quaternion.identity);
        GameObject cup = new GameObject("Cup"); cup.transform.SetParent(handL, false); cup.transform.localPosition = new Vector3(0, .9f, 0);
        Prim(PrimitiveType.Cylinder, "Mug", cup.transform, Vector3.zero, new Vector3(.7f, .45f, .7f), ceramic, Quaternion.identity);
        Prim(PrimitiveType.Cylinder, "Coffee", cup.transform, new Vector3(0, .44f, 0), new Vector3(.6f, .02f, .6f), coffee, Quaternion.identity);
        GameObject book = new GameObject("Book"); book.transform.SetParent(body, false); book.transform.localPosition = new Vector3(0, -.1f, .3f); book.transform.localRotation = Quaternion.Euler(-35, 0, 0);
        Prim(PrimitiveType.Cube, "Cover", book.transform, Vector3.zero, new Vector3(.22f, .27f, .03f), cover, Quaternion.identity);
        Prim(PrimitiveType.Cube, "Pages", book.transform, new Vector3(0, 0, -.012f), new Vector3(.2f, .25f, .02f), ceramic, Quaternion.identity);
        GameObject phones = new GameObject("Headphones"); phones.transform.SetParent(body, false);
        MeshObject("Band", phones.transform, Torus("KomoPhonesBand", .235f, .022f, 48, 6), dark, root.transform.position + Vector3.up * .02f, Quaternion.Euler(90, 0, 0));
        foreach (float side in new[] { -1f, 1f }) Prim(PrimitiveType.Cylinder, "EarCup", phones.transform, new Vector3(side * .23f, .02f, 0), new Vector3(.12f, .03f, .12f), dark, Quaternion.Euler(0, 0, 90));
        cup.SetActive(false); book.SetActive(false); phones.SetActive(false);
        // Speech bubble, billboarded to the local head by CommonsKomo.
        // In front of KOMO (it turns to whoever talks to it), so back-bar shelves and walls do not cut the bubble.
        GameObject bubble = new GameObject("Bubble"); bubble.transform.SetParent(root.transform, false); bubble.transform.localPosition = new Vector3(0, .62f, .4f);
        Prim(PrimitiveType.Quad, "Back", bubble.transform, new Vector3(0, 0, .012f), new Vector3(1.2f, .34f, 1f), bubbleBack, Quaternion.identity);
        TextMesh bubbleText = Text("KomoBubble", "", Vector3.zero, .048f, 0, bubble.transform, Color.white);
        bubbleText.transform.localPosition = Vector3.zero; bubbleText.transform.localRotation = Quaternion.identity;
        bubble.SetActive(false);
        AudioSource voice = root.AddComponent<AudioSource>(); voice.playOnAwake = false; voice.spatialBlend = 1f; voice.minDistance = .6f; voice.maxDistance = 12f; voice.volume = .8f; voice.priority = 80;
        AudioClip[] chirps = new AudioClip[3];
        for (int i = 0; i < 3; i++) chirps[i] = AssetDatabase.LoadAssetAtPath<AudioClip>(AudioDir + "komo_chirp_" + i + ".ogg");
        // Places.
        Transform places = new GameObject("KOMO_Places").transform;
        Transform[] spots = new Transform[K.spots.Length]; Transform[] doors = new Transform[K.spots.Length]; int[] activities = new int[K.spots.Length];
        for (int i = 0; i < K.spots.Length; i++)
        {
            Spot s = K.spots[i];
            spots[i] = Marker("Spot_" + s.name, places, P(s.position), s.yaw);
            doors[i] = Marker("Door_" + s.name, places, P(s.door), s.yaw);
            activities[i] = s.activity;
        }
        komo.body = body; komo.handL = handL; komo.handR = handR; komo.ring = ring; komo.faceMaterial = face;
        komo.cup = cup; komo.book = book; komo.headphones = phones;
        komo.bubble = bubble.transform; komo.bubbleText = bubbleText; komo.bubbleRoot = bubble; komo.voice = voice; komo.chirps = chirps;
        komo.spots = spots; komo.spotActivity = activities; komo.spotDoors = doors; komo.hub = Marker("Hub", places, P(K.hub), 0);
        komo.travelSpeed = K.travel_speed; komo.rideEvery = K.ride_every;
        komo.ride = ride; komo.music = music; komo.settings = settings; komo.state = state; komo.lighting = lighting; komo.timeOfDay = time; komo.comfort = comfort;
        komo.linesEN = KomoLinesEN; komo.linesJP = KomoLinesJP; komo.lineActivity = KomoLineActivity;
        komo.greetEN = KomoGreetEN; komo.greetJP = KomoGreetJP;
        CommonsWorldBuilder.InteractSettings(komo, "Talk to KOMO", 3f);
        return komo;
    }
    // Activity tags: 0 greeter, 1 barista, 2 dj, 3 dancer, 4 stargazer, 5 reader, 6 lounger, 7 gallery, -1 anywhere.
    static readonly int[] KomoLineActivity = { 0, 0, 1, 1, 2, 2, 3, 4, 5, 6, 7, -1, -1, -1, -1, -1, -1 };
    static readonly string[] KomoLinesEN = {
        "Welcome to THE COMMONS!\nSit anywhere. Talk to anyone.",
        "First time? The ORBIT lift\nis next to the portals.",
        "Espresso, tea or soda -\nsame glass, same table.",
        "I can't drink, but I love\nthe sound of the grinder.",
        "This loop follows the lights.\nAsk the host for CYBER!",
        "Quiet room? Ask the host\nfor HOUSE MUSIC.",
        "DISCO lights mean dance time.\nI've been practising.",
        "The city looks best from here.\nOr from orbit.",
        "Reading about tiny worlds.\nWant to be tiny? SIZE LAB!",
        "Best seat in the house:\nyou can see everyone.",
        "These posters change.\nWhat would you show here?",
        "WHAT ARE YOU BUILDING?",
        "The DATA STREAM ride flies\nright through this room!",
        "Hold JUMP inside the gravity\nwell on the sky deck.",
        "Too much glow or motion?\nLOCAL COMFORT + EXPERIENCE.",
        "I'm KOMO. I live here.\nNice to meet you!",
        "Sometimes I ride car A.\nWave if you see me!" };
    static readonly string[] KomoLinesJP = {
        "ようこそ THE COMMONS へ!\nどこに座っても、誰と話しても。",
        "はじめて? ORBITリフトは\nポータルのとなりだよ。",
        "コーヒーでも炭酸でも。\n同じテーブルなら仲間だよ。",
        "飲めないけど、ミルの音が\nだいすきなんだ。",
        "この曲は照明で変わるよ。\nホストにCYBERを頼んでみて!",
        "静かなときはホストに\nHOUSE MUSICを頼んでね。",
        "DISCOの光はダンスの合図。\n練習してたんだ。",
        "街はここから見るのが一番。\nもっと上の軌道からもね。",
        "小さな世界の本を読んでる。\n小さくなるならSIZE LAB!",
        "ここは特等席。\nみんなの顔が見えるんだ。",
        "ポスターは入れ替わるよ。\nきみなら何を飾る?",
        "いま何をつくってる?",
        "DATA STREAMは\nこの部屋の中も飛ぶんだ!",
        "上空デッキの重力井戸で\nジャンプを長押ししてみて。",
        "まぶしい? 酔いそう?\nLOCAL COMFORTとEXPERIENCEへ。",
        "ぼくはKOMO。ここに住んでる。\nよろしくね!",
        "ときどきCAR Aに乗ってるよ。\n見かけたら手をふってね!" };
    static readonly string[] KomoGreetEN = { "Good morning! Coffee's on.", "Hi! Nice day for a ride.", "Good evening! The lights are warm.", "Late-night crew! Welcome.", "Hi, I'm KOMO!\nTalk to me any time (Interact)." };
    static readonly string[] KomoGreetJP = { "おはよう! コーヒー入ってるよ。", "やあ! ライド日和だね。", "こんばんは! いい灯りだね。", "夜ふかし組だね、いらっしゃい。", "ぼくはKOMO!\nいつでも話しかけてね(Interact)。" };
}
#endif
