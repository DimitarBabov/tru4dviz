using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class WindFieldMeshNc : MonoBehaviour
{
    public Material windMaterial;
    public float arrowBaseSize = 0.005f;
    public float arrowLength = 0.05f;
    public DataContainer dataContainer;
    public bool uniformArrowLength = false;
    public float magnitudeScale = 0.1f; // Scale factor for magnitude-based sizing

    public Vector3 lat_origin;
    public Vector3 lon_origin;
    public Vector3 alt_origin;

    void Start()
    {
        StartCoroutine(WaitForDataAndGenerateMesh());
    }

    IEnumerator WaitForDataAndGenerateMesh()
    {
        while (dataContainer == null || !dataContainer.IsLoaded)
        {
            yield return null;
        }
        yield return StartCoroutine(GenerateMeshFromContainer());
    }

    IEnumerator GenerateMeshFromContainer()
    {
        // Check for x_from_origin/y_from_origin
        var xField = dataContainer.GetType().GetField("x_from_origin");
        var yField = dataContainer.GetType().GetField("y_from_origin");
        if (xField == null || yField == null)
        {
            Debug.LogError("DataContainer does not have x_from_origin/y_from_origin fields!");
            yield break;
        }
        var xList = (List<float>)xField.GetValue(dataContainer);
        var yList = (List<float>)yField.GetValue(dataContainer);
        if (xList.Count == 0 || yList.Count == 0)
        {
            Debug.LogError("x_from_origin/y_from_origin are empty!");
            yield break;
        }

        // Arrow mesh template (local space, tip along +Z)
        float baseSize = arrowBaseSize;
        float length = arrowLength;
        Vector3[] arrowVerts = new Vector3[]
        {
            new Vector3(-baseSize, 0, 0),
            new Vector3(0, 0, length),
            new Vector3(baseSize, 0, 0),
            new Vector3(0, baseSize, 0)
        };
        int[] arrowTris = new int[] { 0, 1, 2, 0, 3, 1, 2, 1, 3 };
        Vector2[] arrowUV = new Vector2[]
        {
            new Vector2(0, 0),
            new Vector2(0.5f, 1),
            new Vector2(1, 0),
            new Vector2(0.5f, 0)
        };

        // Find min/max for centering
        float minMsl = float.MaxValue, maxMsl = float.MinValue;
        float minX = float.MaxValue, maxX = float.MinValue;
        float minY = float.MaxValue, maxY = float.MinValue;
        for (int i = 0; i < xList.Count; i++)
        {
            float x = xList[i];
            float y = yList[i];
            float msl = dataContainer.msl[i];
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;
            if (msl < minMsl) minMsl = msl;
            if (msl > maxMsl) maxMsl = msl;
        }

        float centerX = (minX + maxX) * 0.5f;
        float centerY = (minY + maxY) * 0.5f;

        // Initialize origins
        lat_origin = Vector3.zero;
        lon_origin = Vector3.zero;
        alt_origin = new Vector3(0, minMsl, 0);

        // Create corner markers
        CreateCornerMarkers(minX, maxX, minY, maxY, minMsl);

        // Prepare lists for combined mesh
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector2> uvs = new List<Vector2>();
        List<Vector2> uv2s = new List<Vector2>();
        List<Vector2> uv3s = new List<Vector2>();

        for (int i = 0; i < xList.Count; i++)
        {
            float x = xList[i];
            float y = yList[i];
            float msl = dataContainer.msl[i];
            float uNorm = dataContainer.u_norm[i];
            float vNorm = dataContainer.v_norm[i];
            float wNorm = dataContainer.w_norm[i];
            float mag = dataContainer.mag[i];
            float magNorm = dataContainer.mag_norm[i]; // Always use actual magnitude for coloring

            Vector3 tipPos = new Vector3(x, msl, y);
            Vector3 windVec = new Vector3(uNorm, wNorm, vNorm);

            // Use actual magnitude for base size and length calculations with scaling
            float scaledBaseSize = baseSize * mag * magnitudeScale;  // Use actual magnitude with scale factor
            float scaledLength = length * mag * magnitudeScale;      // Use actual magnitude with scale factor

            // Calculate arrow orientation
            Vector3 windDir = windVec.normalized;
            Vector3 basePos = tipPos + windDir * scaledLength;

            // Create local coordinate system for the arrow
            Vector3 forward = windDir;
            Vector3 up = Vector3.up;
            Vector3 right = Vector3.Cross(up, forward).normalized;
            up = Vector3.Cross(forward, right).normalized;

            // Build arrow vertices directly at final positions
            Vector3[] verts = new Vector3[4];
            verts[0] = basePos + right * scaledBaseSize;      // right base corner
            verts[1] = tipPos;                                // tip
            verts[2] = basePos - right * scaledBaseSize;      // left base corner
            verts[3] = basePos + up * scaledBaseSize;         // top base corner

            // Debug logging for first few arrows
            if (i < 5)
            {
                Vector3 delta = tipPos - basePos;
                Debug.Log($"Arrow {i}:");
                Debug.Log($"  Original Magnitude: {mag:F3} m/s");
                Debug.Log($"  Normalized Magnitude: {magNorm:F3}");
                Debug.Log($"  Scaled Length: {scaledLength:F6}");
                Debug.Log($"  Wind Vector (u,w,v): ({uNorm:F3}, {wNorm:F3}, {vNorm:F3})");
                Debug.Log($"  Start Point (tip): {tipPos}");
                Debug.Log($"  End Point (base): {basePos}");
                Debug.Log($"  Delta: {delta}");
            }

            int vertOffset = vertices.Count;
            vertices.AddRange(verts);
            foreach (int t in arrowTris)
                triangles.Add(vertOffset + t);

            uvs.AddRange(arrowUV);

            float mslNorm = (msl - minMsl) / (maxMsl - minMsl);
            // Always use actual magnitude for UV2 (coloring)
            for (int j = 0; j < verts.Length; j++)
                uv2s.Add(new Vector2(magNorm, 0));
            for (int j = 0; j < verts.Length; j++)
                uv3s.Add(new Vector2(mslNorm, 0));

            // Apply uniform length scaling AFTER UV assignment (optional)
            if (uniformArrowLength)
            {
                // Recalculate vertices with uniform length
                Vector3 uniformBasePos = tipPos + windDir * length; // Use base length without magnitude scaling
                
                verts[0] = uniformBasePos + right * baseSize;      // right base corner (uniform size)
                verts[1] = tipPos;                                 // tip (unchanged)
                verts[2] = uniformBasePos - right * baseSize;      // left base corner (uniform size)
                verts[3] = uniformBasePos + up * baseSize;         // top base corner (uniform size)
                
                // Update vertices in the list
                for (int j = 0; j < verts.Length; j++)
                {
                    vertices[vertOffset + j] = verts[j];
                }
            }

            if (i % 2000 == 0)
                yield return null;
        }

        Mesh mesh = new Mesh();
        mesh.indexFormat = vertices.Count > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        mesh.SetVertices(vertices);
        mesh.SetTriangles(triangles, 0);
        mesh.SetUVs(0, uvs);
        mesh.SetUVs(1, uv2s);
        mesh.SetUVs(2, uv3s);
        mesh.RecalculateNormals();

        MeshFilter mf = gameObject.GetComponent<MeshFilter>();
        if (!mf) mf = gameObject.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        MeshRenderer mr = gameObject.GetComponent<MeshRenderer>();
        if (!mr) mr = gameObject.AddComponent<MeshRenderer>();
        mr.sharedMaterial = windMaterial;
    }

    void CreateCornerMarkers(float minX, float maxX, float minY, float maxY, float minMsl)
    {
        // Create parent object for all markers
        GameObject markersParent = new GameObject("Compass Markers");
        markersParent.transform.SetParent(this.transform);

        // Calculate offset distance (5% of the data range - reduced from 10%)
        float offsetX = (maxX - minX) * 0.05f;
        float offsetY = (maxY - minY) * 0.05f;
        float centerX = (minX + maxX) * 0.5f;
        float centerY = (minY + maxY) * 0.5f;

        // Corner markers (white)
        // SW (Southwest) - minimum X, minimum Y - offset southwest
        Vector3 swPos = new Vector3(minX - offsetX, minMsl, minY - offsetY);
        CreateTextMarker("SW", swPos, "SW Corner Marker", Color.white, markersParent.transform);

        // SE (Southeast) - maximum X, minimum Y - offset southeast
        Vector3 sePos = new Vector3(maxX + offsetX, minMsl, minY - offsetY);
        CreateTextMarker("SE", sePos, "SE Corner Marker", Color.white, markersParent.transform);

        // NW (Northwest) - minimum X, maximum Y - offset northwest
        Vector3 nwPos = new Vector3(minX - offsetX, minMsl, maxY + offsetY);
        CreateTextMarker("NW", nwPos, "NW Corner Marker", Color.white, markersParent.transform);

        // NE (Northeast) - maximum X, maximum Y - offset northeast
        Vector3 nePos = new Vector3(maxX + offsetX, minMsl, maxY + offsetY);
        CreateTextMarker("NE", nePos, "NE Corner Marker", Color.white, markersParent.transform);

        // Cardinal direction markers (colored)
        // N (North) - center X, max Y - offset north
        Vector3 nPos = new Vector3(centerX, minMsl, maxY + offsetY);
        CreateTextMarker("N", nPos, "North Marker", Color.blue, markersParent.transform);

        // S (South) - center X, min Y - offset south
        Vector3 sPos = new Vector3(centerX, minMsl, minY - offsetY);
        CreateTextMarker("S", sPos, "South Marker", Color.red, markersParent.transform);

        // W (West) - min X, center Y - offset west
        Vector3 wPos = new Vector3(minX - offsetX, minMsl, centerY);
        CreateTextMarker("W", wPos, "West Marker", Color.green, markersParent.transform);

        // E (East) - max X, center Y - offset east
        Vector3 ePos = new Vector3(maxX + offsetX, minMsl, centerY);
        CreateTextMarker("E", ePos, "East Marker", Color.yellow, markersParent.transform);

        Debug.Log($"Corner Markers Created:");
        Debug.Log($"  SW: X={minX}, Y={minY}, MSL={minMsl}");
        Debug.Log($"  SE: X={maxX}, Y={minY}, MSL={minMsl}");
        Debug.Log($"  NW: X={minX}, Y={maxY}, MSL={minMsl}");
        Debug.Log($"  NE: X={maxX}, Y={maxY}, MSL={minMsl}");
    }

    void CreateTextMarker(string text, Vector3 position, string name, Color color, Transform parent)
    {
        GameObject textObj = new GameObject(name);
        textObj.transform.position = position;
        textObj.transform.SetParent(parent);
        // Rotate text to face upward (90 degrees around X-axis)
        textObj.transform.rotation = Quaternion.Euler(90, 0, 0);
        TextMesh textMesh = textObj.AddComponent<TextMesh>();
        textMesh.text = text;
        textMesh.fontSize = 1000; // 10x bigger than before
        textMesh.color = color;
        textMesh.anchor = TextAnchor.MiddleCenter;
    }
}
