# app.py
# Streamlit Weather App — Open-Meteo (no API key)
# Features:
# - City search (Open-Meteo Geocoding)
# - Optional IP-based geolocation
# - Current, hourly, and 7-day forecast
# - Unit toggle (°C/°F)
# - Simple charts & CSV export

import math
import json
import time
import requests
import pandas as pd
import streamlit as st

# ---------------------------
# Config
# ---------------------------
st.set_page_config(page_title="Weather — Open-Meteo", page_icon="⛅", layout="centered")

@st.cache_data(show_spinner=False, ttl=3600)
def geocode(name: str, count: int = 5, language: str = "zh"):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": count, "language": language, "format": "json"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False, ttl=1800)
def geolocate_ip():
    # 简单的 IP 定位（可替换为你自己的服务）
    try:
        r = requests.get("https://ipapi.co/json/", timeout=10)
        r.raise_for_status()
        j = r.json()
        return {
            "name": j.get("city") or "My Location",
            "latitude": j.get("latitude"),
            "longitude": j.get("longitude"),
            "country": j.get("country_name"),
        }
    except Exception:
        return None

@st.cache_data(show_spinner=False, ttl=900)
def fetch_weather(lat: float, lon: float, tz: str = "auto"):
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "current":
            ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]),
        "hourly":
            ",".join([
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]),
        "daily":
            ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "sunrise",
                "sunset",
                "precipitation_sum",
                "wind_speed_10m_max",
                "weather_code",
            ]),
    }
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# WMO 代码简表
WMO = {
    0: "晴",
    1: "多云少许",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾霭",
    51: "毛毛雨(弱)",
    53: "毛毛雨(中)",
    55: "毛毛雨(强)",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨(小)",
    67: "冻雨(大)",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨(小)",
    81: "阵雨(中)",
    82: "阵雨(大)",
    85: "阵雪(小/中)",
    86: "阵雪(大)",
    95: "雷阵雨(弱/中)",
    96: "雷阵雨伴冰雹(弱)",
    99: "雷阵雨伴冰雹(强)",
}

def wmo_desc(code):
    try:
        return WMO.get(int(code), f"WMO {code}")
    except Exception:
        return str(code)

def to_f(c):
    return c * 9/5 + 32

# ---------------------------
# UI — Sidebar
# ---------------------------
st.sidebar.header("设置")
use_ip = st.sidebar.checkbox("使用 IP 自动定位", value=False)
units = st.sidebar.radio("温度单位", options=["°C", "°F"], index=0, horizontal=True)
lang = st.sidebar.selectbox("语言(地名搜索)", ["zh", "en", "ko"], index=0)
st.sidebar.caption("数据源：Open-Meteo（无需 API Key）")

# ---------------------------
# Location resolve
# ---------------------------
place = None
choices = None

if use_ip:
    place = geolocate_ip()
    if place is None or place.get("latitude") is None:
        st.sidebar.error("IP 定位失败，请改用城市搜索。")
else:
    q = st.sidebar.text_input("搜索城市（中文/英文/韩文均可）", value="Seoul")
    if q.strip():
        geo = geocode(q.strip(), count=6, language=lang)
        results = geo.get("results") if geo else None
        if results:
            choices = {
                f"{i['name']}, {i.get('admin1', '')}, {i.get('country','')} (lat {i['latitude']:.3f}, lon {i['longitude']:.3f})": i
                for i in results
            }
            pick = st.sidebar.selectbox("选择地点", list(choices.keys()), index=0)
            i = choices[pick]
            place = {
                "name": i["name"],
                "latitude": i["latitude"],
                "longitude": i["longitude"],
                "country": i.get("country"),
            }
        else:
            st.sidebar.warning("没有结果，试试英文名或更精确的拼写。")

# ---------------------------
# Main
# ---------------------------
st.title("⛅ 天气查询（Open-Meteo）")

if not place:
    st.info("请在左侧选择地点或开启 IP 定位。")
    st.stop()

lat, lon = place["latitude"], place["longitude"]
st.subheader(f"{place['name']} · {place.get('country','')}")
st.caption(f"坐标：{lat:.4f}, {lon:.4f}")

with st.spinner("获取天气数据中…"):
    data = fetch_weather(lat, lon, tz="auto")

# Current
cur = data.get("current", {})
cur_code = cur.get("weather_code")
cur_desc = wmo_desc(cur_code)
t = cur.get("temperature_2m")
ta = cur.get("apparent_temperature")
wind = cur.get("wind_speed_10m")
hum = cur.get("relative_humidity_2m")
prec = cur.get("precipitation")

if units == "°F":
    t = to_f(t) if t is not None else None
    ta = to_f(ta) if ta is not None else None
    t_unit = "°F"
else:
    t_unit = "°C"

c1, c2, c3, c4 = st.columns(4)
c1.metric("体感温度", f"{ta:.1f}{t_unit}" if ta is not None else "—")
c2.metric("气温", f"{t:.1f}{t_unit}" if t is not None else "—", help=cur_desc)
c3.metric("风速", f"{wind} m/s" if wind is not None else "—")
c4.metric("相对湿度", f"{hum}%" if hum is not None else "—")

st.caption(f"天气概况：{cur_desc} · 降水 {prec} mm/h")

# Hourly
hourly = data.get("hourly", {})
if hourly:
    dfh = pd.DataFrame(hourly)
    # 单位换算
    if units == "°F":
        if "temperature_2m" in dfh:
            dfh["temperature_2m"] = dfh["temperature_2m"].apply(lambda x: to_f(x) if pd.notnull(x) else x)
        if "apparent_temperature" in dfh:
            dfh["apparent_temperature"] = dfh["apparent_temperature"].apply(lambda x: to_f(x) if pd.notnull(x) else x)
    dfh.rename(columns={
        "time": "时间",
        "temperature_2m": f"气温({t_unit})",
        "apparent_temperature": f"体感({t_unit})",
        "precipitation_probability": "降水概率(%)",
        "precipitation": "降水量(mm)",
        "wind_speed_10m": "风速(m/s)",
        "wind_direction_10m": "风向(°)",
        "weather_code": "天气代码",
    }, inplace=True)

    st.subheader("小时预报（未来 48~72 小时）")
    st.line_chart(dfh.set_index("时间")[[f"气温({t_unit})", f"体感({t_unit})"]])
    st.bar_chart(dfh.set_index("时间")[["降水概率(%)"]])

    with st.expander("查看原始小时数据"):
        st.dataframe(dfh, use_container_width=True)
        st.download_button(
            "下载小时数据 CSV",
            dfh.to_csv(index=False).encode("utf-8"),
            file_name="hourly_weather.csv",
            mime="text/csv"
        )

# Daily
daily = data.get("daily", {})
if daily:
    dfd = pd.DataFrame(daily)
    if units == "°F":
        if "temperature_2m_max" in dfd:
            dfd["temperature_2m_max"] = dfd["temperature_2m_max"].apply(lambda x: to_f(x) if pd.notnull(x) else x)
        if "temperature_2m_min" in dfd:
            dfd["temperature_2m_min"] = dfd["temperature_2m_min"].apply(lambda x: to_f(x) if pd.notnull(x) else x)

    dfd.rename(columns={
        "time": "日期",
        "temperature_2m_max": f"最高({t_unit})",
        "temperature_2m_min": f"最低({t_unit})",
        "precipitation_sum": "降水量合计(mm)",
        "wind_speed_10m_max": "最大风速(m/s)",
        "weather_code": "天气代码",
        "sunrise": "日出",
        "sunset": "日落",
    }, inplace=True)

    st.subheader("7 日预报")
    st.area_chart(dfd.set_index("日期")[[f"最高({t_unit})", f"最低({t_unit})"]])

    with st.expander("查看原始 7 日数据"):
        st.dataframe(dfd, use_container_width=True)
        st.download_button(
            "下载 7 日数据 CSV",
            dfd.to_csv(index=False).encode("utf-8"),
            file_name="daily_weather.csv",
            mime="text/csv"
        )

st.caption("⚠️ 本应用仅供参考，请以当地官方发布为准。")
