# -*- coding: utf-8 -*-
"""Page header — enterprise hero card matching reference design."""
from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components

# Page metadata
PAGE_META: dict[str, dict] = {
    "dashboard":          {"icon":"📊","cat_th":"หน้าหลัก","cat_en":"Home","title_th":"แดชบอร์ด","title_en":"Dashboard","desc_th":"ภาพรวมสุขภาพชุมชนแบบ Real-time พร้อม KPI และแผนภูมิสำคัญ","desc_en":"Real-time community health overview with KPIs and charts","cta_th":"ดูภาพรวม →","cta_en":"View Overview →","decor":"📊","tags":["ภาพรวม","KPI","Real-time"]},
    "volunteers":         {"icon":"👥","cat_th":"ประชากร","cat_en":"People","title_th":"อาสาสมัคร (อสม.)","title_en":"Volunteers","desc_th":"จัดการทะเบียน อสม. ค้นหา เพิ่ม และติดตามสถานะการทำงาน","desc_en":"Manage volunteer registry, search, add and track activities","cta_th":"ดูรายชื่อ อสม. →","cta_en":"View Volunteers →","decor":"👥","tags":["อสม.","ทะเบียน"]},
    "households":         {"icon":"🏘️","cat_th":"ประชากร","cat_en":"People","title_th":"ครัวเรือน","title_en":"Households","desc_th":"ทะเบียนครัวเรือนในพื้นที่ชุมชน พร้อมข้อมูลพิกัด GPS","desc_en":"Household registry with GPS coordinates","cta_th":"ดูครัวเรือน →","cta_en":"View Households →","decor":"🏘️","tags":["ครัวเรือน","GPS"]},
    "citizens":           {"icon":"👤","cat_th":"ประชากร","cat_en":"People","title_th":"ประชาชน","title_en":"Citizens","desc_th":"ทะเบียนประชาชน พร้อมกลุ่มเปราะบาง ผู้สูงอายุ และผู้พิการ","desc_en":"Citizen registry with vulnerability, elderly and disabled flags","cta_th":"ดูรายชื่อประชาชน →","cta_en":"View Citizens →","decor":"👤","tags":["ประชาชน","กลุ่มเปราะบาง"]},
    "home_visits":        {"icon":"🏠","cat_th":"การดูแล","cat_en":"Care","title_th":"การเยี่ยมบ้าน","title_en":"Home Visits","desc_th":"บันทึกและติดตามการเยี่ยมบ้านของ อสม. ทุกครั้ง","desc_en":"Record and track all home visits by volunteers","cta_th":"บันทึกการเยี่ยมบ้าน →","cta_en":"New Visit →","decor":"🏠","tags":["เยี่ยมบ้าน","บันทึก"]},
    "referrals":          {"icon":"📤","cat_th":"การดูแล","cat_en":"Care","title_th":"การส่งต่อ","title_en":"Referrals","desc_th":"จัดการการส่งต่อผู้ป่วยไปยังหน่วยบริการสุขภาพ","desc_en":"Manage patient referrals to health service units","cta_th":"ส่งต่อผู้ป่วย →","cta_en":"New Referral →","decor":"📤","tags":["ส่งต่อ","ติดตามผล"]},
    "tasks":              {"icon":"✅","cat_th":"การดูแล","cat_en":"Care","title_th":"การจัดการงาน","title_en":"Task Management","desc_th":"มอบหมายและติดตามงานของ อสม. เพื่อไม่ให้งานตกหล่น","desc_en":"Assign and track tasks so nothing falls through the cracks","cta_th":"ดูงานทั้งหมด →","cta_en":"View All Tasks →","decor":"✅","tags":["งาน","ติดตาม"]},
    "notifications":      {"icon":"🔔","cat_th":"หน้าหลัก","cat_en":"Home","title_th":"ศูนย์รวมการแจ้งเตือนส่วนตัว","title_en":"Personal Notification Center","desc_th":"ติดตามและจัดการการแจ้งเตือนที่สำคัญสำหรับคุณในที่เดียว\nเพื่อไม่ให้พลาดข้อมูลสำคัญจากระบบ","desc_en":"Track and manage all your important notifications in one place\nso you never miss critical updates from the system","cta_th":"ดูการแจ้งเตือนทั้งหมด →","cta_en":"View All Notifications →","decor":"🔔","tags":["แจ้งเตือน"]},
    "announcements":      {"icon":"📢","cat_th":"สื่อสาร","cat_en":"Comms","title_th":"ประกาศและข่าวสาร","title_en":"Announcements","desc_th":"เผยแพร่ประกาศและข่าวสุขภาพไปยังชุมชน","desc_en":"Publish health announcements to the community","cta_th":"ดูประกาศ →","cta_en":"View Announcements →","decor":"📢","tags":["ประกาศ","ข่าว"]},
    "health_profiles":    {"icon":"🩺","cat_th":"การดูแล","cat_en":"Care","title_th":"โปรไฟล์สุขภาพรายบุคคล","title_en":"Individual Health Profiles","desc_th":"บันทึกโปรไฟล์สุขภาพ โรคเรื้อรัง และความต้องการบริการรายบุคคล","desc_en":"Record health profiles, chronic conditions and service needs","cta_th":"ดูโปรไฟล์สุขภาพ →","cta_en":"View Profiles →","decor":"🩺","tags":["สุขภาพ","โรคเรื้อรัง"]},
    "health_assessments": {"icon":"📏","cat_th":"การดูแล","cat_en":"Care","title_th":"การประเมินสุขภาพ","title_en":"Health Assessments","desc_th":"บันทึกผลการวัด BMI ความดัน ชีพจร และอุณหภูมิรายบุคคล","desc_en":"Record BMI, blood pressure, pulse and temperature readings","cta_th":"ประเมินสุขภาพ →","cta_en":"New Assessment →","decor":"📏","tags":["ประเมิน","BMI"]},
    "early_warning":      {"icon":"⚠️","cat_th":"การดูแล","cat_en":"Care","title_th":"ระบบเตือนภัยชุมชน","title_en":"Community Early Warning System","desc_th":"เตือนภัยอัตโนมัติเมื่อตรวจพบสัญญาณเสี่ยงในชุมชน","desc_en":"Automatic alerts when risk signals are detected in the community","cta_th":"ดูการแจ้งเตือน →","cta_en":"View Alerts →","decor":"⚠️","tags":["เตือนภัย","อัตโนมัติ"]},
    "cvi":                {"icon":"📊","cat_th":"การดูแล","cat_en":"Care","title_th":"ดัชนีความเปราะบางชุมชน (CVI)","title_en":"Community Vulnerability Index (CVI)","desc_th":"คะแนนลำดับความสำคัญในการสนับสนุนชุมชน 0-100 ไม่ใช่การวินิจฉัยโรค","desc_en":"Community support priority score 0-100. Not a medical diagnosis.","cta_th":"ดูคะแนน CVI →","cta_en":"View CVI Scores →","decor":"📊","tags":["CVI","ความเปราะบาง"]},
    "gis":                {"icon":"🗺️","cat_th":"แผนที่","cat_en":"Maps","title_th":"แผนที่ GIS ชุมชน","title_en":"Community GIS Map","desc_th":"แผนที่และ Heatmap แสดงการกระจายประชากรในพื้นที่","desc_en":"Map and heatmaps showing population distribution","cta_th":"เปิดแผนที่ →","cta_en":"Open Map →","decor":"🗺️","tags":["GIS","Heatmap"]},
    "reports":            {"icon":"📋","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"รายงาน","title_en":"Reports","desc_th":"สร้างและดาวน์โหลดรายงานข้อมูลสุขภาพชุมชน PDF และ Excel","desc_en":"Generate and download community health reports in PDF and Excel","cta_th":"สร้างรายงาน →","cta_en":"Generate Report →","decor":"📋","tags":["รายงาน","Excel"]},
    "ai_assistant":       {"icon":"🤖","cat_th":"AI","cat_en":"AI","title_th":"ผู้ช่วย AI สุขภาพชุมชน","title_en":"Community Health AI Assistant","desc_th":"สรุปรายงาน วิเคราะห์แนวโน้ม และข้อเสนอแนะด้วย AI ไม่วินิจฉัยโรค","desc_en":"AI summaries, trend analysis and recommendations. No diagnosis.","cta_th":"ถาม AI →","cta_en":"Ask AI →","decor":"🤖","tags":["AI","รายงาน"]},
    "executive_v2":       {"icon":"🧠","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"ศูนย์บัญชาการอัจฉริยะ","title_en":"Executive Intelligence Center","desc_th":"13 โมดูลวิเคราะห์ขั้นสูง GIS ประชากร ความเสี่ยง และ Insight อัตโนมัติ","desc_en":"13 advanced analytics modules with automatic insights","cta_th":"ดูภาพรวมผู้บริหาร →","cta_en":"View Executive Dashboard →","decor":"🧠","tags":["Executive","AI","GIS"]},
    "user_management":    {"icon":"👥","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"ระบบจัดการผู้ใช้งาน","title_en":"User Management System","desc_th":"สร้าง แก้ไข กำหนดสิทธิ์ และจัดการผู้ใช้งาน 10 บทบาท RBAC","desc_en":"Create, edit, set permissions and manage users with 10-role RBAC","cta_th":"จัดการผู้ใช้ →","cta_en":"Manage Users →","decor":"👥","tags":["ผู้ใช้","RBAC"]},
    "system_health":      {"icon":"💚","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"แดชบอร์ดสุขภาพระบบ","title_en":"System Health Dashboard","desc_th":"ตรวจสอบสถานะฐานข้อมูล เวลาตอบสนอง และความสมบูรณ์ของระบบ","desc_en":"Monitor database status, response time and system health","cta_th":"ตรวจสอบระบบ →","cta_en":"Check System →","decor":"💚","tags":["ระบบ","ฐานข้อมูล"]},
    "quick_actions":      {"icon":"⚡","cat_th":"หน้าหลัก","cat_en":"Home","title_th":"ดำเนินการด่วน","title_en":"Quick Actions","desc_th":"เข้าถึงฟังก์ชันที่ใช้บ่อยที่สุดได้ทันทีในคลิกเดียว","desc_en":"Access the most-used functions instantly in one click","cta_th":"เลือกการดำเนินการ →","cta_en":"Select Action →","decor":"⚡","tags":["ด่วน","ลัด"]},
    "workspace":          {"icon":"🖥️","cat_th":"หน้าหลัก","cat_en":"Home","title_th":"พื้นที่ทำงานของฉัน","title_en":"My Workspace","desc_th":"หน้าที่เพิ่งดูล่าสุดและรายการโปรดส่วนตัวของคุณ","desc_en":"Your recently visited pages and personal favorites","cta_th":"ดูพื้นที่ทำงาน →","cta_en":"Open Workspace →","decor":"🖥️","tags":["Workspace","โปรด"]},
    "help_center":        {"icon":"❓","cat_th":"ความช่วยเหลือ","cat_en":"Help","title_th":"ศูนย์ความช่วยเหลือ","title_en":"Help Center","desc_th":"คู่มือการใช้งาน FAQ Release Notes และข้อมูลเวอร์ชันระบบ","desc_en":"User guide, FAQ, release notes and system version info","cta_th":"ดูคู่มือ →","cta_en":"View Guide →","decor":"❓","tags":["คู่มือ","FAQ"]},
    "followups":          {"icon":"🔁","cat_th":"การดูแล","cat_en":"Care","title_th":"ระบบติดตามอัตโนมัติ","title_en":"Auto Follow-Up System","desc_th":"ติดตามประชาชนที่ยังไม่ได้รับการเยี่ยมบ้านนานกว่า 90 วัน","desc_en":"Follow up citizens not visited in over 90 days automatically","cta_th":"ดูการติดตาม →","cta_en":"View Follow-Ups →","decor":"🔁","tags":["ติดตาม","อัตโนมัติ"]},
    "projects":           {"icon":"🏗️","cat_th":"บริการ","cat_en":"Services","title_th":"โครงการชุมชน","title_en":"Community Projects","desc_th":"บริหารโครงการสุขภาพชุมชน ติดตามงบประมาณและสถานะโครงการ","desc_en":"Manage community health projects, budgets and status","cta_th":"ดูโครงการ →","cta_en":"View Projects →","decor":"🏗️","tags":["โครงการ","งบประมาณ"]},
    "analytics":          {"icon":"📉","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"วิเคราะห์ข้อมูลระบบ","title_en":"System Analytics","desc_th":"ประสิทธิภาพ อสม. แนวโน้มการเยี่ยมบ้าน และสถิติการส่งต่อ","desc_en":"Volunteer efficiency, visit trends and referral statistics","cta_th":"ดูการวิเคราะห์ →","cta_en":"View Analytics →","decor":"📉","tags":["วิเคราะห์","แนวโน้ม"]},
    "scorecards":         {"icon":"🏆","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"คะแนนชุมชน","title_en":"Community Scorecards","desc_th":"จัดอันดับชุมชนตามผลการดำเนินงานด้านสุขภาพรายเดือน","desc_en":"Monthly community performance rankings and scores","cta_th":"ดูอันดับชุมชน →","cta_en":"View Rankings →","decor":"🏆","tags":["อันดับ","ชุมชน"]},
    "population_health":  {"icon":"🌏","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"วิเคราะห์สุขภาพประชากร","title_en":"Population Health Analytics","desc_th":"พีระมิดอายุ อัตราพึ่งพิง การกระจายโรคเรื้อรัง และพยากรณ์","desc_en":"Age pyramid, dependency ratio, disease distribution and forecast","cta_th":"ดูข้อมูลประชากร →","cta_en":"View Population →","decor":"🌏","tags":["ประชากร","พีระมิด"]},
    "risk_stratification":{"icon":"🎯","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"การจัดลำดับความสำคัญ","title_en":"Priority Stratification","desc_th":"คะแนนลำดับความสำคัญในการสนับสนุนชุมชน 0-100","desc_en":"Community support priority scoring 0-100","cta_th":"ดูลำดับความสำคัญ →","cta_en":"View Priorities →","decor":"🎯","tags":["ลำดับ","คะแนน"]},
    "quality_management": {"icon":"✅","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"ระบบจัดการคุณภาพ","title_en":"Quality Management System","desc_th":"ตัวชี้วัดคุณภาพงานสาธารณสุขชุมชนรายเดือนเทียบกับเป้าหมาย","desc_en":"Monthly quality indicators vs targets","cta_th":"ดูตัวชี้วัด →","cta_en":"View Indicators →","decor":"✅","tags":["คุณภาพ","ตัวชี้วัด"]},
    "performance":        {"icon":"📈","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"การบริหารผลการปฏิบัติงาน","title_en":"Performance Management","desc_th":"KPI อัตราการเยี่ยมบ้าน การส่งต่อสำเร็จ กิจกรรม อสม.","desc_en":"KPI for visit rates, referral completion, volunteer activity","cta_th":"ดู KPI →","cta_en":"View KPIs →","decor":"📈","tags":["KPI","ผลการปฏิบัติ"]},
    "outcomes":           {"icon":"📊","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"ติดตามผลลัพธ์กรณีศึกษา","title_en":"Case Outcome Tracking","desc_th":"บันทึกและติดตามผลลัพธ์กรณีที่ให้บริการ ดีขึ้น คงที่ แย่ลง","desc_en":"Record and track case outcomes: improved, stable, deteriorated","cta_th":"ดูผลลัพธ์ →","cta_en":"View Outcomes →","decor":"📊","tags":["ผลลัพธ์","ติดตาม"]},
    "capacity_planning":  {"icon":"📐","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"การวางแผนกำลังคนชุมชน","title_en":"Community Capacity Planning","desc_th":"วิเคราะห์สัดส่วน อสม. ต่อประชาชน ภาระงาน และช่องว่างความครอบคลุม","desc_en":"Volunteer-to-population ratio, workload and coverage gap analysis","cta_th":"ดูแผนกำลังคน →","cta_en":"View Capacity →","decor":"📐","tags":["กำลังคน","วางแผน"]},
    "community_health":   {"icon":"🏘️","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"แดชบอร์ดสุขภาพชุมชน","title_en":"Community Health Dashboard","desc_th":"ภาพรวมสุขภาพชุมชน สถิติประชากร โรคเรื้อรัง และความเปราะบาง","desc_en":"Community health overview, population stats, chronic diseases","cta_th":"ดูสุขภาพชุมชน →","cta_en":"View Community Health →","decor":"🏘️","tags":["ชุมชน","สถิติ"]},
    "health_analytics":   {"icon":"📊","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"วิเคราะห์ข้อมูลสุขภาพ","title_en":"Health Data Analytics","desc_th":"แผนภูมิ BMI ความดันโลหิต พีระมิดอายุ และแนวโน้มรายเดือน","desc_en":"BMI, blood pressure, age pyramid and monthly trend charts","cta_th":"ดูการวิเคราะห์ →","cta_en":"View Analytics →","decor":"📊","tags":["วิเคราะห์","BMI"]},
    "health_trends":      {"icon":"📈","cat_th":"การดูแล","cat_en":"Care","title_th":"แนวโน้มสุขภาพรายบุคคล","title_en":"Individual Health Trends","desc_th":"กราฟแสดงแนวโน้มสุขภาพตามเวลา น้ำหนัก BMI ความดัน ชีพจร","desc_en":"Health trend charts over time: weight, BMI, BP, pulse","cta_th":"ดูแนวโน้ม →","cta_en":"View Trends →","decor":"📈","tags":["กราฟ","แนวโน้ม"]},
    "elderly_monitoring": {"icon":"👴","cat_th":"การดูแล","cat_en":"Care","title_th":"ระบบติดตามผู้สูงอายุ","title_en":"Elderly Monitoring System","desc_th":"ติดตามผู้สูงอายุในชุมชน ผู้ติดบ้าน และผู้ไม่มีผู้ดูแล","desc_en":"Monitor elderly, homebound and uncared-for citizens in the community","cta_th":"ดูผู้สูงอายุ →","cta_en":"View Elderly →","decor":"👴","tags":["ผู้สูงอายุ","ติดบ้าน"]},
    "import_engine":      {"icon":"📥","cat_th":"บริการ","cat_en":"Services","title_th":"เครื่องมือนำเข้าข้อมูล","title_en":"Data Import Engine","desc_th":"นำเข้าข้อมูลจาก Excel CSV หรือ JSON พร้อมตรวจสอบความถูกต้อง","desc_en":"Import data from Excel, CSV or JSON with validation","cta_th":"นำเข้าข้อมูล →","cta_en":"Import Data →","decor":"📥","tags":["นำเข้า","Excel"]},
    "security_dashboard": {"icon":"🔒","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"แดชบอร์ดความปลอดภัย","title_en":"Security Dashboard","desc_th":"ติดตามสถานะความปลอดภัย ประวัติ Login และการแจ้งเตือน","desc_en":"Monitor security status, login history and alerts","cta_th":"ดูความปลอดภัย →","cta_en":"View Security →","decor":"🔒","tags":["ความปลอดภัย","Login"]},
    "settings":           {"icon":"⚙️","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"การตั้งค่าระบบ","title_en":"System Settings","desc_th":"ตั้งค่าองค์กร โซนเวลา นโยบายรหัสผ่าน และขีดจำกัด AI","desc_en":"Configure organization, timezone, password policy and AI limits","cta_th":"ตั้งค่า →","cta_en":"Configure →","decor":"⚙️","tags":["ตั้งค่า","ระบบ"]},
    "audit":              {"icon":"📋","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"บันทึกการตรวจสอบ","title_en":"Audit Log","desc_th":"ประวัติการดำเนินการทุกครั้งในระบบ ใครทำอะไร เมื่อไหร่","desc_en":"Full audit trail of all system actions, who did what and when","cta_th":"ดู Audit Log →","cta_en":"View Audit Log →","decor":"📋","tags":["Audit","ประวัติ"]},
    "feature_flags":      {"icon":"🚩","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"สวิตช์ฟีเจอร์","title_en":"Feature Flags","desc_th":"เปิด-ปิดฟีเจอร์ของระบบโดยไม่ต้องรีสตาร์ทแอปพลิเคชัน","desc_en":"Toggle system features without restarting the application","cta_th":"จัดการฟีเจอร์ →","cta_en":"Manage Features →","decor":"🚩","tags":["ฟีเจอร์","สวิตช์"]},
    "scheduler":          {"icon":"⏰","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"ตัวจัดการงานอัตโนมัติ","title_en":"Automated Job Scheduler","desc_th":"ตั้งเวลางานอัตโนมัติ Follow-Up Warning Engine CVI และ Risk Score","desc_en":"Schedule automated jobs: Follow-Up, Warning Engine, CVI and Risk Score","cta_th":"จัดการงาน →","cta_en":"Manage Jobs →","decor":"⏰","tags":["อัตโนมัติ","เวลา"]},
    "backup":             {"icon":"💾","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"สำรองและกู้คืนข้อมูล","title_en":"Backup and Data Recovery","desc_th":"ส่งออกข้อมูลทั้งหมดเป็น JSON หรือ Excel สำหรับสำรองข้อมูล","desc_en":"Export all data as JSON or Excel for backup","cta_th":"สำรองข้อมูล →","cta_en":"Backup Data →","decor":"💾","tags":["สำรอง","ส่งออก"]},
    "error_tracking":     {"icon":"🐛","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"ระบบติดตามข้อผิดพลาด","title_en":"Error Tracking System","desc_th":"บันทึกและติดตามข้อผิดพลาด INFO WARNING ERROR CRITICAL","desc_en":"Log and track errors at INFO, WARNING, ERROR and CRITICAL levels","cta_th":"ดูข้อผิดพลาด →","cta_en":"View Errors →","decor":"🐛","tags":["Error","Debug"]},
    "app_logs":           {"icon":"📜","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"บันทึกกิจกรรมแอปพลิเคชัน","title_en":"Application Activity Logs","desc_th":"บันทึกกิจกรรมผู้ใช้ทุกครั้ง สำหรับ Audit และการตรวจสอบ","desc_en":"Full user activity log for auditing and compliance","cta_th":"ดูบันทึก →","cta_en":"View Logs →","decor":"📜","tags":["Log","Audit"]},
    "database_tools":     {"icon":"🗄️","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"เครื่องมือจัดการฐานข้อมูล","title_en":"Database Management Tools","desc_th":"สถิติ Record ประวัติ Migration ขนาดฐานข้อมูล และเวอร์ชัน PostgreSQL","desc_en":"Record stats, migration history, DB size and PostgreSQL version","cta_th":"ดูฐานข้อมูล →","cta_en":"View Database →","decor":"🗄️","tags":["ฐานข้อมูล","Migration"]},
    "versioning":         {"icon":"📦","cat_th":"ผู้ดูแล","cat_en":"Admin","title_th":"ข้อมูลเวอร์ชันระบบ","title_en":"System Version Information","desc_th":"เวอร์ชันปัจจุบัน โมดูลที่ติดตั้ง สถานะ Migration และฟีเจอร์","desc_en":"Current version, installed modules, migration status and features","cta_th":"ดูเวอร์ชัน →","cta_en":"View Version →","decor":"📦","tags":["เวอร์ชัน","โมดูล"]},
    "campaigns":          {"icon":"📣","cat_th":"บริการ","cat_en":"Services","title_th":"แคมเปญสุขภาพ","title_en":"Health Campaigns","desc_th":"จัดการแคมเปญรณรงค์สุขภาพชุมชน","desc_en":"Manage community health awareness campaigns","cta_th":"ดูแคมเปญ →","cta_en":"View Campaigns →","decor":"📣","tags":["แคมเปญ"]},
    "executive":          {"icon":"🎯","cat_th":"วิเคราะห์","cat_en":"Insights","title_th":"ศูนย์บัญชาการผู้บริหาร","title_en":"Executive Command Center","desc_th":"KPI ระดับสูง แนวโน้มประชากร กรณีความสำคัญสูง และอันดับชุมชน","desc_en":"High-level KPIs, population trends, priority cases and rankings","cta_th":"ดูภาพรวม →","cta_en":"View Dashboard →","decor":"🎯","tags":["ผู้บริหาร","KPI"]},
}

COLORS = {
    "หน้าหลัก":"#2563EB","Home":"#2563EB",
    "ประชากร":"#7C3AED","People":"#7C3AED",
    "การดูแล":"#059669","Care":"#059669",
    "บริการ":"#D97706","Services":"#D97706",
    "แผนที่":"#0D9488","Maps":"#0D9488",
    "วิเคราะห์":"#DC2626","Insights":"#DC2626",
    "AI":"#9333EA",
    "ผู้ดูแล":"#475569","Admin":"#475569",
    "สื่อสาร":"#2563EB","Comms":"#2563EB",
    "ความช่วยเหลือ":"#6366F1","Help":"#6366F1",
}


def render_page_header(page_key: str) -> None:
    is_thai = st.session_state.get("lang","TH") == "TH"

    meta = PAGE_META.get(page_key, {
        "icon":"📄","cat_th":"ระบบ","cat_en":"System",
        "title_th":page_key.replace("_"," ").title(),
        "title_en":page_key.replace("_"," ").title(),
        "desc_th":"MKI Community Health Platform",
        "desc_en":"MKI Community Health Platform",
        "cta_th":"เปิด →","cta_en":"Open →",
        "decor":"📄","tags":[],
    })

    icon   = meta["icon"]
    cat    = meta["cat_th"]   if is_thai else meta["cat_en"]
    title  = meta["title_th"] if is_thai else meta["title_en"]
    desc   = meta["desc_th"]  if is_thai else meta["desc_en"]
    cta    = meta["cta_th"]   if is_thai else meta["cta_en"]
    decor  = meta.get("decor", icon)
    accent = COLORS.get(cat, "#2563EB")
    breadcrumb = f"🏠 หน้าหลัก  ›  {cat}" if is_thai else f"🏠 Home  ›  {cat}"
    desc_html  = desc.replace("\n","<br>")

    # Build pill tags
    pills_html = "".join(
        f'<span style="display:inline-block;'
        f'{"background:"+accent+";color:#fff" if i==0 else "background:#F0F4FF;color:"+accent+";border:1px solid #DBEAFE"};'
        f'font-size:13px;font-weight:600;padding:6px 16px;border-radius:20px;margin-right:8px;">{tag}</span>'
        for i, tag in enumerate(meta.get("tags",[]))
    )

    html = (
        f'<div style="background:#ffffff;border-radius:20px;padding:28px 32px 24px;'
        f'box-shadow:0 4px 24px rgba(15,23,42,0.08),0 0 0 1px #E8ECF0;'
        f'margin-bottom:24px;position:relative;overflow:hidden;">'

        # Accent bar left
        f'<div style="position:absolute;top:0;left:0;width:5px;height:100%;'
        f'background:{accent};border-radius:20px 0 0 20px;"></div>'

        # Background decoration (large emoji watermark)
        f'<div style="position:absolute;right:32px;top:50%;transform:translateY(-50%);'
        f'font-size:96px;opacity:0.06;user-select:none;pointer-events:none;'
        f'filter:blur(1px);">{decor}</div>'

        # Content
        f'<div style="padding-left:12px;">'

        # Icon box + breadcrumb row
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">'
        f'<div style="width:52px;height:52px;background:#F0F4FF;border-radius:14px;'
        f'display:flex;align-items:center;justify-content:center;font-size:26px;'
        f'box-shadow:0 2px 8px rgba(37,99,235,0.12);flex-shrink:0;">{icon}</div>'
        f'<div style="font-size:14px;font-weight:500;color:#64748B;">'
        f'<span style="color:{accent};font-weight:600;">{breadcrumb.split("›")[0].strip()}</span>'
        f'<span style="color:#94A3B8;"> › </span>'
        f'<span style="color:{accent};font-weight:600;">{cat}</span>'
        f'</div></div>'

        # Title
        f'<div style="font-size:28px;font-weight:800;color:#0F172A;line-height:1.2;'
        f'margin-bottom:10px;letter-spacing:-0.3px;">{title}</div>'

        # Description
        f'<div style="font-size:15px;color:#475569;line-height:1.65;'
        f'margin-bottom:18px;max-width:600px;">{desc_html}</div>'

        # CTA button + pills
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'<button style="background:{accent};color:#fff;border:none;'
        f'border-radius:12px;padding:11px 22px;font-size:14px;font-weight:600;'
        f'cursor:pointer;box-shadow:0 4px 14px rgba(37,99,235,0.3);'
        f'letter-spacing:0.2px;">{cta}</button>'
        f'{pills_html}'
        f'</div>'

        f'</div></div>'
    )

    st.markdown(html, unsafe_allow_html=True)
