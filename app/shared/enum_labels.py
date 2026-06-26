# -*- coding: utf-8 -*-
"""Bilingual labels for all enum dropdowns."""
from __future__ import annotations
import streamlit as st


def _th() -> bool:
    return st.session_state.get("lang", "TH") == "TH"


def income_labels() -> dict:
    th = _th()
    return {
        "very_low": "รายได้น้อยมาก" if th else "Very Low Income",
        "low":      "รายได้น้อย"     if th else "Low Income",
        "medium":   "รายได้ปานกลาง"  if th else "Medium Income",
        "high":     "รายได้สูง"      if th else "High Income",
        "":         "ไม่ระบุ"        if th else "Not specified",
    }


def housing_labels() -> dict:
    th = _th()
    return {
        "own":    "บ้านตัวเอง"   if th else "Own",
        "rent":   "เช่า"         if th else "Rent",
        "public": "บ้านพักรัฐ"   if th else "Public Housing",
        "other":  "อื่นๆ"        if th else "Other",
        "":       "ไม่ระบุ"      if th else "Not specified",
    }


def gender_labels() -> dict:
    th = _th()
    return {
        "male":   "ชาย"          if th else "Male",
        "female": "หญิง"         if th else "Female",
        "other":  "อื่นๆ"        if th else "Other",
        "":       "ไม่ระบุ"      if th else "Not specified",
    }


def volunteer_status_labels() -> dict:
    th = _th()
    return {
        "active":    "ใช้งาน"    if th else "Active",
        "inactive":  "ไม่ใช้งาน" if th else "Inactive",
        "suspended": "พักงาน"    if th else "Suspended",
        "":          "ไม่ระบุ"   if th else "Not specified",
    }


def referral_status_labels() -> dict:
    th = _th()
    return {
        "pending":     "รอดำเนินการ"   if th else "Pending",
        "in_progress": "กำลังดำเนินการ" if th else "In Progress",
        "completed":   "เสร็จสิ้น"     if th else "Completed",
        "cancelled":   "ยกเลิก"        if th else "Cancelled",
        "":            "ไม่ระบุ"        if th else "Not specified",
    }


def referral_target_labels() -> dict:
    th = _th()
    return {
        "hospital":      "โรงพยาบาล"      if th else "Hospital",
        "health_center": "สถานีอนามัย"     if th else "Health Center",
        "municipality":  "เทศบาล/อบต."    if th else "Municipality",
        "ngo":           "องค์กรพัฒนาเอกชน" if th else "NGO",
        "":              "ไม่ระบุ"          if th else "Not specified",
    }


def visit_type_labels() -> dict:
    th = _th()
    return {
        "routine":    "เยี่ยมบ้านปกติ"     if th else "Routine Visit",
        "follow_up":  "ติดตามผล"           if th else "Follow Up",
        "emergency":  "ฉุกเฉิน"            if th else "Emergency",
        "referral":   "ส่งต่อ"             if th else "Referral",
        "":           "ไม่ระบุ"             if th else "Not specified",
    }


def task_status_labels() -> dict:
    th = _th()
    return {
        "new":         "งานใหม่"           if th else "New",
        "assigned":    "มอบหมายแล้ว"       if th else "Assigned",
        "in_progress": "กำลังดำเนินการ"   if th else "In Progress",
        "completed":   "เสร็จสิ้น"         if th else "Completed",
        "overdue":     "เกินกำหนด"         if th else "Overdue",
        "cancelled":   "ยกเลิก"            if th else "Cancelled",
        "":            "ไม่ระบุ"            if th else "Not specified",
    }


def task_priority_labels() -> dict:
    th = _th()
    return {
        "low":      "ต่ำ"        if th else "Low",
        "medium":   "ปานกลาง"   if th else "Medium",
        "high":     "สูง"        if th else "High",
        "critical": "วิกฤต"      if th else "Critical",
        "":         "ไม่ระบุ"   if th else "Not specified",
    }


def province_region_labels() -> dict:
    th = _th()
    return {
        "active":    "ใช้งาน"    if th else "Active",
        "inactive":  "ไม่ใช้งาน" if th else "Inactive",
        "":          "ทั้งหมด"   if th else "All",
    }


def assessment_type_labels() -> dict:
    th = _th()
    return {
        "routine":    "ปกติ"       if th else "Routine",
        "follow_up":  "ติดตาม"     if th else "Follow Up",
        "annual":     "ประจำปี"    if th else "Annual",
        "":           "ไม่ระบุ"    if th else "Not specified",
    }
