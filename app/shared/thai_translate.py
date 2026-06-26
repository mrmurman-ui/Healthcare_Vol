# -*- coding: utf-8 -*-
"""Global Thai/EN translation helper — imported by all service modules."""
from __future__ import annotations
import streamlit as st


def is_thai() -> bool:
    return st.session_state.get("lang", "TH") == "TH"


def t(th: str, en: str) -> str:
    """Return Thai or English string based on session language."""
    return th if is_thai() else en


# Common field labels used across multiple pages
COMMON = {
    # Actions
    "save":          ("💾 บันทึก",              "💾 Save"),
    "cancel":        ("ยกเลิก",                 "Cancel"),
    "search":        ("🔍 ค้นหา",               "🔍 Search"),
    "add_new":       ("➕ เพิ่มใหม่",            "➕ Add New"),
    "edit":          ("✏️ แก้ไข",               "✏️ Edit"),
    "delete":        ("🗑️ ลบ",                  "🗑️ Delete"),
    "export":        ("📥 ส่งออก",              "📥 Export"),
    "refresh":       ("⟳ รีเฟรช",              "⟳ Refresh"),
    "select":        ("เลือก",                   "Select"),
    "all":           ("ทั้งหมด",                 "All"),
    "notes":         ("หมายเหตุ",                "Notes"),
    "status":        ("สถานะ",                   "Status"),
    "type":          ("ประเภท",                  "Type"),
    "date":          ("วันที่",                  "Date"),
    "name":          ("ชื่อ",                    "Name"),
    "description":   ("คำอธิบาย",               "Description"),
    "severity":      ("ระดับความรุนแรง",         "Severity"),
    "open":          ("เปิด",                    "Open"),
    "acknowledged":  ("รับทราบแล้ว",             "Acknowledged"),
    "resolved":      ("แก้ไขแล้ว",              "Resolved"),
    "active":        ("ใช้งาน",                  "Active"),
    "inactive":      ("ไม่ใช้งาน",              "Inactive"),
    "completed":     ("เสร็จสิ้น",              "Completed"),
    "planning":      ("วางแผน",                  "Planning"),
    "critical":      ("วิกฤต",                   "Critical"),
    "high":          ("สูง",                     "High"),
    "medium":        ("ปานกลาง",                "Medium"),
    "low":           ("ต่ำ",                     "Low"),
    "no_data":       ("ไม่มีข้อมูล",             "No data available"),
    "filter":        ("กรอง",                    "Filter"),
    "category":      ("หมวดหมู่",                "Category"),
    "total":         ("ทั้งหมด",                 "Total"),
    "yes":           ("ใช่",                     "Yes"),
    "no":            ("ไม่",                     "No"),
    # Health measurements
    "height_cm":     ("ส่วนสูง (ซม.)",           "Height (cm)"),
    "weight_kg":     ("น้ำหนัก (กก.)",           "Weight (kg)"),
    "bmi":           ("BMI",                      "BMI"),
    "waist_cm":      ("รอบเอว (ซม.)",            "Waist (cm)"),
    "bp_sys":        ("ความดันโลหิต (ตัวบน)",    "BP Systolic"),
    "bp_dia":        ("ความดันโลหิต (ตัวล่าง)", "BP Diastolic"),
    "pulse":         ("ชีพจร",                   "Pulse Rate"),
    "temp":          ("อุณหภูมิ (°C)",            "Temperature (°C)"),
    "blood_sugar":   ("น้ำตาลในเลือด (ไม่บังคับ)","Blood Sugar (optional)"),
    # Common section headers
    "measurements":  ("การวัด",                   "Measurements"),
    "population":    ("ประชากร",                  "Population"),
    "elderly":       ("ผู้สูงอายุ (60+)",         "Elderly (60+)"),
    "disabled":      ("ผู้พิการ",                 "Disabled"),
    "bedridden":     ("ติดเตียง",                 "Bedridden"),
    "living_alone":  ("อยู่คนเดียว",              "Living Alone"),
    "home_visits":   ("การเยี่ยมบ้าน",            "Home Visits"),
    "referrals":     ("การส่งต่อ",               "Referrals"),
    "open_alerts":   ("การแจ้งเตือนที่เปิดอยู่", "Open Alerts"),
    "volunteers":    ("อาสาสมัคร",                "Volunteers"),
    "citizens":      ("ประชาชน",                  "Citizens"),
}


def tc(key: str) -> str:
    """Look up a common translation key."""
    pair = COMMON.get(key, (key, key))
    return pair[0] if is_thai() else pair[1]
