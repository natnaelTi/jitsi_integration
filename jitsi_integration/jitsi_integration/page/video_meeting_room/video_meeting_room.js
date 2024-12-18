frappe.pages['video-meeting-room'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Video Meeting Room',
		single_column: true
	});

	// Add meeting container
	$(wrapper).find('.page-content').html('<div id="meet"></div>');

	// Get meeting details from URL
	const meetingId = frappe.utils.get_url_arg('meeting');

	if (!meetingId) {
		frappe.throw(__('Meeting ID is required'));
		return;
	}

	// Load Jitsi Meet API
	const script = document.createElement('script');
	script.src = 'https://meet.jit.si/external_api.js';
	script.async = true;
	script.onload = function () {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Video Meeting',
				name: meetingId
			},
			callback: function (r) {
				if (r.message) {
					const meeting = r.message;
					initJitsiMeet(meeting);
				}
			}
		});
	};
	document.body.appendChild(script);
};

function initJitsiMeet(meeting) {
	const domain = frappe.db.get_single_value('Jitsi Settings', 'jitsi_server_url') || 'meet.jit.si';
	const options = {
		roomName: meeting.meeting_id,
		width: '100%',
		height: '100%',
		parentNode: document.querySelector('#meet'),
		userInfo: {
			displayName: frappe.session.user_fullname,
			email: frappe.session.user
		},
		configOverwrite: {
			startWithAudioMuted: true,
			startWithVideoMuted: true
		},
		interfaceConfigOverwrite: {
			TOOLBAR_BUTTONS: [
				'microphone', 'camera', 'closedcaptions', 'desktop', 'fullscreen',
				'fodeviceselection', 'hangup', 'profile', 'chat', 'recording',
				'livestreaming', 'etherpad', 'sharedvideo', 'settings', 'raisehand',
				'videoquality', 'filmstrip', 'invite', 'feedback', 'stats', 'shortcuts',
				'tileview', 'videobackgroundblur', 'download', 'help', 'mute-everyone'
			]
		}
	};

	const api = new JitsiMeetExternalAPI(domain, options);

	// Handle meeting events
	api.addEventListeners({
		readyToClose: function () {
			frappe.set_route('List', 'Video Meeting');
		}
	});
}