using System.Collections.Generic;
using UnityEngine;

public class DataContainer : MonoBehaviour
{
    public List<float> lat = new List<float>();
    public List<float> lon = new List<float>();
    public List<float> msl = new List<float>();
    public List<float> u_norm = new List<float>();
    public List<float> v_norm = new List<float>();
    public List<float> w_norm = new List<float>();
    public List<float> mag = new List<float>();
    public List<float> mag_norm = new List<float>();

    public Vector2 uMinMax;
    public Vector2 vMinMax;
    public Vector2 wMinMax;
    public Vector2 magMinMax;

    public bool IsLoaded { get; protected set; } = false;
} 