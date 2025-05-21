using System.Collections.Generic;
using UnityEngine;
using System.Globalization;
using System.IO;

public class HrrrDataContainer : MonoBehaviour
{
    public List<float> lat = new List<float>();
    public List<float> lon = new List<float>();
    public List<float> gh = new List<float>();
    public List<float> u_norm = new List<float>();
    public List<float> v_norm = new List<float>();
    public List<float> w_norm = new List<float>();
    public List<float> mag = new List<float>();
    public List<float> mag_norm = new List<float>();

    public Vector2 uMinMax;
    public Vector2 vMinMax;
    public Vector2 wMinMax;
    public Vector2 magMinMax;

    public string resourceCsvName = "fort_worth_levels_1_to_15_unity";
    public string minmaxResourceCsvName = "fort_worth_levels_1_to_15_minmax";

    // --- New for image loading ---
    public bool loadFromImages = false;
    public string imgResourceFolder = "img_encoded_hrr_levels";
    public int minLevel = 1;
    public int maxLevel = 15;

    [Header("Assign in Inspector: Level images (PNG) and meta JSONs (TextAsset)")]
    public List<Texture2D> levelImages; // PNGs for each level, in order
    public List<TextAsset> levelMetas;  // JSON meta for each level, in order

    public bool IsLoaded { get; private set; } = false;

    void Start()
    {
        if (loadFromImages)
        {
            // Use inspector lists if both are non-empty and of equal length
            if (levelImages != null && levelMetas != null && levelImages.Count > 0 && levelMetas.Count > 0 && levelImages.Count == levelMetas.Count)
            {
                LoadFromInspectorAssets();
            }
            else
            {
                LoadFromImagesAndJson();
            }
        }
        else
        {
            if (lat.Count == 0 || lon.Count == 0)
            {
                LoadFromResource();
            }
            LoadMinMaxFromResource();
        }
    }

    public void LoadFromResource()
    {
        TextAsset csvData = Resources.Load<TextAsset>(resourceCsvName);
        if (csvData == null)
        {
            Debug.LogError("CSV resource not found: " + resourceCsvName);
            return;
        }
        string[] lines = csvData.text.Split('\n');
        if (lines.Length < 2) return;
        // Find column indices
        string[] header = lines[0].Trim().Split(',');
        int idxLat = System.Array.IndexOf(header, "latitude");
        int idxLon = System.Array.IndexOf(header, "longitude");
        int idxGh = System.Array.IndexOf(header, "gh[gpm]");
        int idxU = System.Array.IndexOf(header, "u_norm");
        int idxV = System.Array.IndexOf(header, "v_norm");
        int idxW = System.Array.IndexOf(header, "w_norm");
        int idxMag = System.Array.IndexOf(header, "mag");
        int idxMagNorm = System.Array.IndexOf(header, "mag_norm");
        float uMin = float.MaxValue, uMax = float.MinValue;
        float vMin = float.MaxValue, vMax = float.MinValue;
        float wMin = float.MaxValue, wMax = float.MinValue;
        float magMin = float.MaxValue, magMax = float.MinValue;
        for (int i = 1; i < lines.Length; i++)
        {
            string line = lines[i].Trim();
            if (string.IsNullOrEmpty(line)) continue;
            string[] row = line.Split(',');
            float fLat = float.Parse(row[idxLat], System.Globalization.CultureInfo.InvariantCulture);
            float fLon = float.Parse(row[idxLon], System.Globalization.CultureInfo.InvariantCulture);
            float fGh = float.Parse(row[idxGh], System.Globalization.CultureInfo.InvariantCulture);
            float fU = float.Parse(row[idxU], System.Globalization.CultureInfo.InvariantCulture);
            float fV = float.Parse(row[idxV], System.Globalization.CultureInfo.InvariantCulture);
            float fW = float.Parse(row[idxW], System.Globalization.CultureInfo.InvariantCulture);
            float fMag = float.Parse(row[idxMag], System.Globalization.CultureInfo.InvariantCulture);
            float fMagNorm = float.Parse(row[idxMagNorm], System.Globalization.CultureInfo.InvariantCulture);
            lat.Add(fLat);
            lon.Add(fLon);
            gh.Add(fGh);
            u_norm.Add(fU);
            v_norm.Add(fV);
            w_norm.Add(fW);
            mag.Add(fMag);
            mag_norm.Add(fMagNorm);
            if (fU < uMin) uMin = fU;
            if (fU > uMax) uMax = fU;
            if (fV < vMin) vMin = fV;
            if (fV > vMax) vMax = fV;
            if (fW < wMin) wMin = fW;
            if (fW > wMax) wMax = fW;
            if (fMag < magMin) magMin = fMag;
            if (fMag > magMax) magMax = fMag;
        }
        uMinMax = new Vector2(uMin, uMax);
        vMinMax = new Vector2(vMin, vMax);
        wMinMax = new Vector2(wMin, wMax);
        magMinMax = new Vector2(magMin, magMax);
        IsLoaded = true;
    }

    public void LoadMinMaxFromResource()
    {
        TextAsset minmaxData = Resources.Load<TextAsset>(minmaxResourceCsvName);
        if (minmaxData == null)
        {
            Debug.LogError("MinMax CSV resource not found: " + minmaxResourceCsvName);
            return;
        }
        string[] lines = minmaxData.text.Split('\n');
        for (int i = 1; i < lines.Length; i++)
        {
            string line = lines[i].Trim();
            if (string.IsNullOrEmpty(line)) continue;
            string[] row = line.Split(',');
            if (row.Length < 3) continue;
            string varName = row[0];
            float min = float.Parse(row[1], System.Globalization.CultureInfo.InvariantCulture);
            float max = float.Parse(row[2], System.Globalization.CultureInfo.InvariantCulture);
            switch (varName)
            {
                case "u": uMinMax = new Vector2(min, max); break;
                case "v": vMinMax = new Vector2(min, max); break;
                case "w": wMinMax = new Vector2(min, max); break;
                case "mag": magMinMax = new Vector2(min, max); break;
            }
        }
        IsLoaded = true;
    }

    [System.Serializable]
    public class LevelMeta
    {
        public int level;
        public float u_min, u_max, v_min, v_max, w_min, w_max, gh_min, gh_max;
        public float min_lat, max_lat, min_lon, max_lon;
        public int num_lat, num_lon;
    }

    public void LoadFromImagesAndJson()
    {
        lat.Clear(); lon.Clear(); gh.Clear();
        u_norm.Clear(); v_norm.Clear(); w_norm.Clear();
        mag.Clear(); mag_norm.Clear();

        float uGlobalMin = float.MaxValue, uGlobalMax = float.MinValue;
        float vGlobalMin = float.MaxValue, vGlobalMax = float.MinValue;
        float wGlobalMin = float.MaxValue, wGlobalMax = float.MinValue;
        float magGlobalMin = float.MaxValue, magGlobalMax = float.MinValue;
        List<float> tempMag = new List<float>();

        // First pass: decode all valid points, compute min/max
        for (int level = minLevel; level <= maxLevel; level++)
        {
            string metaPath = imgResourceFolder + "/fort_worth_level" + level + "_meta";
            TextAsset metaJson = Resources.Load<TextAsset>(metaPath);
            if (metaJson == null) continue;
            LevelMeta meta = JsonUtility.FromJson<LevelMeta>(metaJson.text);
            string imgPath = imgResourceFolder + "/fort_worth_level" + level + "_img";
            Texture2D tex = Resources.Load<Texture2D>(imgPath);
            if (tex == null) continue;
            Color32[] pixels = tex.GetPixels32();
            int numLat = meta.num_lat;
            int numLon = meta.num_lon;
            float dLat = (meta.max_lat - meta.min_lat) / (numLat - 1);
            float dLon = (meta.max_lon - meta.min_lon) / (numLon - 1);
            for (int y = 0; y < numLat; y++)
            {
                for (int x = 0; x < numLon; x++)
                {
                    int idx = y * numLon + x;
                    if (idx >= pixels.Length) continue;
                    Color32 c = pixels[idx];
                    if (c.r == 255 && c.g == 255 && c.b == 255 && c.a == 255) continue;
                    float uVal = meta.u_min + (c.r / 255f) * (meta.u_max - meta.u_min);
                    float vVal = meta.v_min + (c.g / 255f) * (meta.v_max - meta.v_min);
                    float wVal = meta.w_min + (c.b / 255f) * (meta.w_max - meta.w_min);
                    float ghN = c.a / 255f;
                    float ghVal = meta.gh_min + ghN * (meta.gh_max - meta.gh_min);
                    float magVal = Mathf.Sqrt(uVal * uVal + vVal * vVal + wVal * wVal);
                    // Update min/max
                    if (uVal < uGlobalMin) uGlobalMin = uVal;
                    if (uVal > uGlobalMax) uGlobalMax = uVal;
                    if (vVal < vGlobalMin) vGlobalMin = vVal;
                    if (vVal > vGlobalMax) vGlobalMax = vVal;
                    if (wVal < wGlobalMin) wGlobalMin = wVal;
                    if (wVal > wGlobalMax) wGlobalMax = wVal;
                    if (magVal < magGlobalMin) magGlobalMin = magVal;
                    if (magVal > magGlobalMax) magGlobalMax = magVal;
                    // Store for normalization
                    lat.Add(meta.max_lat - y * dLat);
                    lon.Add(meta.min_lon + x * dLon);
                    gh.Add(ghVal);
                    u_norm.Add(uVal); // will normalize after
                    v_norm.Add(vVal);
                    w_norm.Add(wVal);
                    mag.Add(magVal);
                    tempMag.Add(magVal);
                }
            }
        }
        // Normalize u, v, w, mag
        for (int i = 0; i < u_norm.Count; i++)
        {
            u_norm[i] = (u_norm[i] - uGlobalMin) / (uGlobalMax - uGlobalMin);
            v_norm[i] = (v_norm[i] - vGlobalMin) / (vGlobalMax - vGlobalMin);
            w_norm[i] = (w_norm[i] - wGlobalMin) / (wGlobalMax - wGlobalMin);
            mag_norm.Add((mag[i] - magGlobalMin) / (magGlobalMax - magGlobalMin));
        }
        uMinMax = new Vector2(uGlobalMin, uGlobalMax);
        vMinMax = new Vector2(vGlobalMin, vGlobalMax);
        wMinMax = new Vector2(wGlobalMin, wGlobalMax);
        magMinMax = new Vector2(magGlobalMin, magGlobalMax);
        IsLoaded = true;
    }

    public void LoadFromInspectorAssets()
    {
        lat.Clear(); lon.Clear(); gh.Clear();
        u_norm.Clear(); v_norm.Clear(); w_norm.Clear();
        mag.Clear(); mag_norm.Clear();

        float uGlobalMin = float.MaxValue, uGlobalMax = float.MinValue;
        float vGlobalMin = float.MaxValue, vGlobalMax = float.MinValue;
        float wGlobalMin = float.MaxValue, wGlobalMax = float.MinValue;
        List<float> allMag = new List<float>();

        // First pass: find global min/max for u, v, w
        for (int i = 0; i < levelImages.Count; i++)
        {
            if (levelImages[i] == null || levelMetas[i] == null) continue;
            LevelMeta meta = JsonUtility.FromJson<LevelMeta>(levelMetas[i].text);
            Texture2D tex = levelImages[i];
            Color32[] pixels = tex.GetPixels32();
            if (i == 0) // Only for level 1 (index 0)
            {
                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                sb.AppendLine($"All RGBA values for image {i} (level 1):");
                for (int p = 0; p < pixels.Length; p++)
                {
                    Color32 c = pixels[p];
                    sb.Append($"({c.r},{c.g},{c.b},{c.a}) ");
                    if ((p + 1) % 16 == 0) sb.AppendLine(); // new line every 16 pixels
                }
                Debug.Log(sb.ToString());
            }
            int numLat = meta.num_lat;
            int numLon = meta.num_lon;
            for (int y = 0; y < numLat; y++)
            {
                for (int x = 0; x < numLon; x++)
                {
                    int idx = y * numLon + x;
                    if (idx >= pixels.Length) continue;
                    Color32 c = pixels[idx];
                    if (c.r == 255 && c.g == 255 && c.b == 255 && c.a == 255) continue;
                    float uVal = meta.u_min + (c.r / 255f) * (meta.u_max - meta.u_min);
                    float vVal = meta.v_min + (c.g / 255f) * (meta.v_max - meta.v_min);
                    float wVal = meta.w_min + (c.b / 255f) * (meta.w_max - meta.w_min);
                    if (uVal < uGlobalMin) uGlobalMin = uVal;
                    if (uVal > uGlobalMax) uGlobalMax = uVal;
                    if (vVal < vGlobalMin) vGlobalMin = vVal;
                    if (vVal > vGlobalMax) vGlobalMax = vVal;
                    if (wVal < wGlobalMin) wGlobalMin = wVal;
                    if (wVal > wGlobalMax) wGlobalMax = wVal;
                }
            }
        }

        List<float> tempLat = new List<float>();
        List<float> tempLon = new List<float>();
        List<float> tempGh = new List<float>();
        List<float> tempUNorm = new List<float>();
        List<float> tempVNorm = new List<float>();
        List<float> tempWNorm = new List<float>();
        List<float> tempMag = new List<float>();

        // Second pass: fill lists and normalize mag
        for (int i = 0; i < levelImages.Count; i++)
        {
            if (levelImages[i] == null || levelMetas[i] == null) continue;
            LevelMeta meta = JsonUtility.FromJson<LevelMeta>(levelMetas[i].text);
            Texture2D tex = levelImages[i];
            Color32[] pixels = tex.GetPixels32();
            int numLat = meta.num_lat;
            int numLon = meta.num_lon;
            float dLat = (meta.max_lat - meta.min_lat) / (numLat - 1);
            float dLon = (meta.max_lon - meta.min_lon) / (numLon - 1);

            for (int y = 0; y < numLat; y++)
            {
                for (int x = 0; x < numLon; x++)
                {
                    int idx = y * numLon + x;
                    if (idx >= pixels.Length) continue;
                    Color32 c = pixels[idx];
                    if (c.r == 255 && c.g == 255 && c.b == 255 && c.a == 255) continue;
                    float uVal = meta.u_min + (c.r / 255f) * (meta.u_max - meta.u_min);
                    float vVal = meta.v_min + (c.g / 255f) * (meta.v_max - meta.v_min);
                    float wVal = meta.w_min + (c.b / 255f) * (meta.w_max - meta.w_min);
                    float uN = (uVal - uGlobalMin) / (uGlobalMax - uGlobalMin);
                    float vN = (vVal - vGlobalMin) / (vGlobalMax - vGlobalMin);
                    float wN = (wVal - wGlobalMin) / (wGlobalMax - wGlobalMin);
                    float ghN = c.a / 255f;
                    float ghVal = meta.gh_min + ghN * (meta.gh_max - meta.gh_min);
                    float magVal = Mathf.Sqrt(uVal * uVal + vVal * vVal + wVal * wVal);
                    tempLat.Add(meta.max_lat - y * dLat);
                    tempLon.Add(meta.min_lon + x * dLon);
                    tempGh.Add(ghVal);
                    tempUNorm.Add(uN);
                    tempVNorm.Add(vN);
                    tempWNorm.Add(wN);
                    tempMag.Add(magVal);
                    allMag.Add(magVal);
                }
            }
        }

        // Compute global min/max for mag
        float magGlobalMin = float.MaxValue, magGlobalMax = float.MinValue;
        foreach (float m in allMag)
        {
            if (m < magGlobalMin) magGlobalMin = m;
            if (m > magGlobalMax) magGlobalMax = m;
        }
        magMinMax = new Vector2(magGlobalMin, magGlobalMax);
        uMinMax = new Vector2(uGlobalMin, uGlobalMax);
        vMinMax = new Vector2(vGlobalMin, vGlobalMax);
        wMinMax = new Vector2(wGlobalMin, wGlobalMax);

        // Final pass: fill lists and normalize mag
        for (int i = 0; i < tempLat.Count; i++)
        {
            lat.Add(tempLat[i]);
            lon.Add(tempLon[i]);
            gh.Add(tempGh[i]);
            u_norm.Add(tempUNorm[i]);
            v_norm.Add(tempVNorm[i]);
            w_norm.Add(tempWNorm[i]);
            mag.Add(tempMag[i]);
            float magN = (tempMag[i] - magGlobalMin) / (magGlobalMax - magGlobalMin);
            mag_norm.Add(magN);
        }
        IsLoaded = true;
        Debug.Log("Loaded valid points: " + lat.Count);
    }
} 