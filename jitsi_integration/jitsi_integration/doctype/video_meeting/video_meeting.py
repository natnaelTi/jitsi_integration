# Copyright (c) 2024, Selfmade Cloud Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import uuid
from frappe.utils import get_url

class VideoMeeting(Document):
	def before_save(self):
		if not self.meeting_id:
			# Generate a unique meeting ID
			self.meeting_id = str(uuid.uuid4())
		# Generate meeting URL
		base_url = frappe.db.get_single_value('Jitsi Settings', 'jitsi_server_url') or 'meet.jit.si'
		self.meeting_url = f"https://{base_url}/{self.meeting_id}"
	
	def after_insert(self):
		frappe.logger().debug("Video Meeting after_insert triggered")
		self.notify_participants()
	
	def notify_participants(self):
		try:
			subject = f"Video Meeting: {self.meeting_title}"
			message = f"""
			<p>You have been invited to a video meeting.</p>
			
			<h3>Meeting Details:</h3>
			<ul>
				<li><strong>Title:</strong> {self.meeting_title}</li>
				<li><strong>Time:</strong> {self.scheduled_time}</li>
				<li><strong>Duration:</strong> {self.duration} minutes</li>
				<li><strong>Host:</strong> {frappe.db.get_value("User", self.host, "full_name")}</li>
			</ul>
			
			<p>Join meeting: <a href="{self.meeting_url}">{self.meeting_url}</a></p>
			"""
			
			# Get participant emails with validation
			valid_participants = []
			invalid_participants = []
			
			if self.participants:
				for p in self.participants:
					if p.email:
						# Basic email validation
						if frappe.utils.validate_email_address(p.email):
							valid_participants.append(p.email)
						else:
							invalid_participants.append(p.email)
			
			# Add host's email if not in participants
			host_email = frappe.db.get_value("User", self.host, "email")
			if host_email and host_email not in valid_participants:
				if frappe.utils.validate_email_address(host_email):
					valid_participants.append(host_email)
				else:
					invalid_participants.append(host_email)
				
			if valid_participants:
				frappe.logger().debug(f"Sending meeting invitation to: {valid_participants}")
				
				# Send emails individually to handle failures better
				for email in valid_participants:
					try:
						frappe.sendmail(
							recipients=[email],  # Send to one recipient at a time
							subject=subject,
							message=message,
							reference_doctype=self.doctype,
							reference_name=self.name,
							send_priority=1,
							now=True
						)
					except Exception as e:
						invalid_participants.append(email)
						frappe.log_error(
							f"Failed to send meeting notification to {email}: {str(e)}", 
							"Video Meeting Individual Notification Error"
						)
				
				# Show success/failure message
				if invalid_participants:
					frappe.msgprint(
						f"""Meeting invitation sent to {len(valid_participants) - len(invalid_participants)} participants.<br>
						Failed to send to the following email(s): {', '.join(invalid_participants)}""",
						indicator='orange',
						title='Partial Success'
					)
				else:
					frappe.msgprint(
						f"Meeting invitation sent to {len(valid_participants)} participants",
						indicator='green'
					)
			else:
				frappe.msgprint("No valid participants to notify", indicator='red')
				
			# Log invalid emails for review
			if invalid_participants:
				frappe.log_error(
					f"Invalid or failed email addresses for meeting {self.name}: {invalid_participants}",
					"Invalid Meeting Participants"
				)
				
		except Exception as e:
			frappe.log_error(
				f"Failed to send meeting notifications: {str(e)}", 
				"Video Meeting Notification Error"
			)
			frappe.msgprint("Failed to send meeting notifications. Please check error logs.")