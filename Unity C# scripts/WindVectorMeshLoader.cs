using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class WindVectorMeshLoader : MonoBehaviour
{
    public Material windMaterial;
    public float arrowBaseSize = 0.005f;
    public float arrowLength = 0.05f;
    public HrrrDataContainer dataContainer;

    void Start()
    {
        StartCoroutine(GenerateMeshFromContainer());
    }

    IEnumerator GenerateMeshFromContainer()
    {
        if (dataContainer == null || dataContainer.lat.Count == 0)
        {
            Debug.LogError("No data in HrrrDataContainer!");
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

        // Find min/max/mean for centering
        float minGh = float.MaxValue, maxGh = float.MinValue;
        float minLon = float.MaxValue, maxLon = float.MinValue;
        float minLat = float.MaxValue, maxLat = float.MinValue;
        for (int i = 0; i < dataContainer.lat.Count; i++)
        {
            float lon = dataContainer.lon[i];
            float lat = dataContainer.lat[i];
            float gh = dataContainer.gh[i];
            if (gh < minGh) minGh = gh;
            if (gh > maxGh) maxGh = gh;
            if (lon < minLon) minLon = lon;
            if (lon > maxLon) maxLon = lon;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
        }
        float centerLon = (minLon + maxLon) * 0.5f;
        float centerLat = (minLat + maxLat) * 0.5f;

        // Prepare lists for combined mesh
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector2> uvs = new List<Vector2>();
        List<Vector2> uv2s = new List<Vector2>();
        List<Vector2> uv3s = new List<Vector2>();

        for (int i = 0; i < dataContainer.lat.Count; i++)
        {
            float lat = dataContainer.lat[i];
            float lon = dataContainer.lon[i];
            float gh = dataContainer.gh[i];
            float uNorm = dataContainer.u_norm[i];
            float vNorm = dataContainer.v_norm[i];
            float wNorm = dataContainer.w_norm[i];
            float mag = dataContainer.mag[i];
            float magNorm = dataContainer.mag_norm[i];

            // Convert lat/lon/gh to Unity world coordinates (customize as needed)
            Vector3 pos = new Vector3(
                lon - centerLon,
                (gh - minGh) * 0.0001f,
                lat - centerLat
            );
            // Reconstruct wind vector from normalized values and min/max if needed
            // Here, we use normalized values directly for direction
            Vector3 windVec = new Vector3(uNorm, wNorm, vNorm);

            // Scale arrow by magnitude
            float scaledBaseSize = baseSize * magNorm;
            float scaledLength = length * magNorm;
            Vector3[] verts = new Vector3[arrowVerts.Length];
            for (int j = 0; j < arrowVerts.Length; j++)
                verts[j] = arrowVerts[j];
            // Scale
            for (int j = 0; j < verts.Length; j++)
            {
                verts[j].x *= (scaledBaseSize / baseSize);
                verts[j].y *= (scaledLength / length);
                verts[j].z *= (scaledBaseSize / baseSize);
            }
            // Rotate to wind direction
            Quaternion rot = windVec != Vector3.zero ? Quaternion.LookRotation(windVec.normalized, Vector3.up) : Quaternion.identity;
            for (int j = 0; j < verts.Length; j++)
                verts[j] = rot * verts[j];
            // Translate to position
            for (int j = 0; j < verts.Length; j++)
                verts[j] += pos;
            // Add to combined mesh
            int vertOffset = vertices.Count;
            vertices.AddRange(verts);
            foreach (int t in arrowTris)
                triangles.Add(vertOffset + t);
            uvs.AddRange(arrowUV);
            float ghNorm = (gh - minGh) / (maxGh - minGh);
            for (int j = 0; j < verts.Length; j++)
                uv2s.Add(new Vector2(magNorm, 0));
            for (int j = 0; j < verts.Length; j++)
                uv3s.Add(new Vector2(ghNorm, 0));

            if (i % 2000 == 0)
                yield return null;
        }

        // Create combined mesh
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
} 