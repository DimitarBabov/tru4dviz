using System.Collections.Generic;
using UnityEngine;

public class NcDataContainerImgs : DataContainer
{
    public string imgResourceFolder = "img_encoded_nc_levels";
    // Set subFolder to one of: "high_levels_img_encoded", "mid_levels_img_encoded", "low_levels_img_encoded"
    public string subFolder = "mid_levels_img_encoded";
    public int minLevel = 0;
    public int maxLevel = 2;

    void Start()
    {
        LoadFromImagesAndJson();
    }

    [System.Serializable]
    public class LevelMeta
    {
        public int level_index;
        public float u_min, u_max, v_min, v_max, w_min, w_max;
        public float alt_min, alt_max;
        public float min_lat, max_lat, min_lon, max_lon;
        public int num_lat, num_lon;
    }

    public void LoadFromImagesAndJson()
    {
        lat.Clear(); lon.Clear(); msl.Clear();
        u_norm.Clear(); v_norm.Clear(); w_norm.Clear();
        mag.Clear(); mag_norm.Clear();

        float uGlobalMin = float.MaxValue, uGlobalMax = float.MinValue;
        float vGlobalMin = float.MaxValue, vGlobalMax = float.MinValue;
        float wGlobalMin = float.MaxValue, wGlobalMax = float.MinValue;
        float magGlobalMin = float.MaxValue, magGlobalMax = float.MinValue;
        List<float> tempMag = new List<float>();

        // Determine prefix based on subFolder
        string prefix = "mid_level";
        if (subFolder.Contains("high")) prefix = "high_level";
        else if (subFolder.Contains("low")) prefix = "low_level";

        // First pass: decode all valid points, compute min/max
        for (int level = minLevel; level <= maxLevel; level++)
        {
            string metaPath = subFolder + "/" + prefix + level + "_meta";
            TextAsset metaJson = Resources.Load<TextAsset>(metaPath);
            if (metaJson == null) continue;
            LevelMeta meta = JsonUtility.FromJson<LevelMeta>(metaJson.text);
            string imgPath = subFolder + "/" + prefix + level + "_img";
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
                    // Decode alpha in [0.1, 0.9] range
                    float altNorm = Mathf.Clamp01((c.a - 1f) / 253f);
                    float altVal = meta.alt_min + altNorm * (meta.alt_max - meta.alt_min);
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
                    msl.Add(altVal); // Assign alt to msl
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
} 