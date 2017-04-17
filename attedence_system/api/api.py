from __future__ import unicode_literals
import json
import frappe
from datetime import datetime
from frappe.utils import nowdate

@frappe.whitelist(allow_guest=True)
def create_attendance_record(employee,att_date,time):

	emp_name = frappe.db.get_value("Employee",{"name":employee},"employee_name")
	if emp_name :
		try:
			att_record = frappe.db.get_value("Attendance",{"att_date":att_date,"status":"Present","employee":employee},"name")
			if not att_record :
				attendance_doc = frappe.new_doc("Attendance")
				attendance_doc.employee = employee
				attendance_doc.att_date = att_date
				attendance_doc.save(ignore_permissions=True)
				#attendance_doc.submit()

			attendance_log = frappe.new_doc("Attendance Log")
			attendance_log.employee = employee
			attendance_log.att_date = att_date
			attendance_log.time = time
			attendance_log.save(ignore_permissions=True)
			print "attendance_log.name",attendance_log.name
			frappe.db.commit()
			return "Welcome",frappe.db.get_value("Employee",{"name":employee},"employee_name")
		except Exception, e:
			raise e

	else:
			return "Invalid Employee ID"
	

@frappe.whitelist(allow_guest=True)
# To mark the status as "Absent" of the employees, those are on leave .
def status_absent():
	emp_name = frappe.db.sql("""select employee, employee_name, company from `tabEmployee` where employee  NOT IN ( select employee from `tabAttendance` where att_date = curdate())""", as_dict=1)
	
	if emp_name:
		try:
			for emp_details in emp_name:
				attendance_doc = frappe.new_doc("Attendance")
				attendance_doc.att_date = nowdate()
				attendance_doc.employee = emp_details["employee"]          
				attendance_doc.employee_name = emp_details["employee_name"]        
				attendance_doc.company = emp_details["company"]	         
				attendance_doc.status = "Absent"
				attendance_doc.save(ignore_permissions=True)
				#attendance_doc.submit()
			
		except Exception, e:
			print frappe.get_traceback()
			raise e


@frappe.whitelist(allow_guest=True)
# to calculate total time duration in in_time (mintime) and out_time(maxtime)
def time_calculations():
	times = frappe.db.sql(""" select att.name as name1, att.status as status, attlog.employee as employee,
							  attlog.employee_name as employee_name, att.att_date as a_date, convert(attlog.cnt, signed) as counts, 
							  attlog.max as maxtime, attlog.min as mintime
							  from `tabAttendance` as att , 
							  (select employee, employee_name, max(time) as max, min(time) as min, count(*) as cnt  
							  from `tabAttendance Log` where att_date = curdate() group by employee) 
							  as attlog where attlog.employee =att.employee and att_date = curdate() """, 
							  as_dict=1)	
	
	if times:
		try:
			for time_details in times:
				if time_details["status"] != "Absent":

					if (time_details["counts"] % 2) == 0:	
															
						attendance = frappe.get_doc("Attendance", time_details["name1"])

						attendance.time_in = time_details["mintime"]
						attendance.time_out = time_details["maxtime"]

						time_diff=frappe.utils.data.time_diff(str(time_details['a_date'])+" "+str(time_details["maxtime"]),str(time_details['a_date'])+" "+str(time_details["mintime"]))
							
						attendance.total_time_spent = time_diff

						attendance.save(ignore_permissions=True)
						attendance.submit()

					else:
							
						attendance = frappe.get_doc("Attendance", time_details["name1"])
							
						attendance.time_in = time_details["mintime"]
						attendance.time_out = "19:00:00"

						time_diff = frappe.utils.data.time_diff("19:00:00",time_details["mintime"])
												
						attendance.total_time_spent = time_diff
							
						attendance.save(ignore_permissions=True)
						attendance.submit()

				else:
					attendance = frappe.get_doc("Attendance", time_details["name1"])
					attendance.save(ignore_permissions=True)
					attendance.submit()

		except Exception, e:
			print frappe.get_traceback()
			raise e 
		