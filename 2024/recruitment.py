import openreview
from credentials import credentials
from utils import send_email
import csv

""" 
    Connecting to OpenReview  
"""

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=credentials['user'],
                           password=credentials['pw'])
venue_id = 'auai.org/UAI/2024/Conference'


""" 
    Extracting the list of invited area chairs that have accepted or rejected the invitation 
"""

invited_id = '/Area_Chairs/Invited'
acs_id = '/Area_Chairs'
declined_id = '/Declined'

all_acs = list(openreview.tools.iterget_groups(client, id=venue_id+invited_id))[0]
print(all_acs.members)

accepted_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id))[0]
print(accepted_acs)

declined_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id+declined_id))[0]
print(declined_acs)

non_response = list(set(all_acs.members).difference(set(accepted_acs.members).union(declined_acs.members)))


""" Decline messages: when an area chair/ reviewer declines the invite, they can add a comment. """

decline_messages = list(client.get_all_notes(invitation='auai.org/UAI/2024/Conference/Area_Chairs/-/Recruitment'))
decline_messages_rev = list(client.get_all_notes(invitation='auai.org/UAI/2024/Conference/Reviewers/-/Recruitment'))


with open('decline_messages-rev.csv', 'w') as f:
    headers = set.union(*[set(decline_messages_rev[i].content.keys()) for i in range(len(decline_messages_rev))])
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for i in range(len(decline_messages_rev)):
        # if decline_messages[i].content['response']['value'] == 'No':
        w.writerow(decline_messages_rev[i].content)


""" get AC profiles without 'expertise' field """

acc_ac_id = accepted_acs.members
ac_with_empty_expertise = []
i = 0
for ac_id in acc_ac_id:
    ac_prof = client.get_profile(ac_id)
    try:
        ac_prof.content['expertise']
        # print(f'i={i}, '+str(len(ac_prof.content['expertise'])))
    except KeyError:
        print(f'i={i}, '+str(ac_prof.id))
        ac_with_empty_expertise += [ac_prof.id]
    i += 1

""" Send an email to AC profiles without expertise field to ask them to fill it in """
recipients = ac_with_empty_expertise
message = f"""
We thank you for accepting our invitation to serve as Area Chair for UAI 2024. We look forward to working with you.

As we are getting prepared for the next steps, we kindly ask you to update your OpenReview profile with your specific field of expertise. This will improve matching papers to your expertise during the assignments phase.

To update your field of expertise, follow the steps below:
OpenReview Profile-> Edit profile -> Expertise
"""
title = '[UAI 2024] Area Chair Expertise Field'
send_email(client=client, recipients=recipients, title=title, message=message)


def get_invite_link(id, role):
    """
    :param id: email or OpenReview ID
    :param role: 'Area Chair' or 'Reviewer'
    :return: invitation link
    """
    prev_mes = client.get_all_messages(to=id, subject='[UAI 2024] Invitation to serve as ' + role)[0]['content']['text']
    return 'https' + prev_mes.split('https')[1].split('\n\nIf you have')[0]


""" Send reminders for invitations """

all_acs = list(openreview.tools.iterget_groups(client, id=venue_id+invited_id))[0]
accepted_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id))[0]
declined_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id+declined_id))[0]
non_response = list(set(all_acs.members).difference(set(accepted_acs.members).union(declined_acs.members)))
role = 'Area Chair'
title = '[UAI 2024] Reminder: Invitation to serve as ' + role
msg = 'invitation msg'
recipients = []
send_email(client=client, recipients=recipients, title=title, message=message)


""" Gather the non-response ACs with their names and usernames"""

all_acs = list(openreview.tools.iterget_groups(client, id=venue_id+invited_id))[0]
accepted_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id))[0]
declined_acs = list(openreview.tools.iterget_groups(client, id=venue_id+acs_id+declined_id))[0]
non_response = list(set(all_acs.members).difference(set(accepted_acs.members).union(declined_acs.members)))

headers = client.get_profile(non_response[0]).content['names'][0].keys()
with open('nonresponse2.csv', 'w') as f:
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for i in range(len(non_response)):
        try:
            prf = client.get_profile(non_response[i])
            w.writerow(prf.content['names'][0])
        except:
            print(non_response[i])

""" Getting bounced reviewer invitations: sometimes the invitation email may bounce and not arrive at the invitee"""

mes_failed = client.get_messages(subject='[UAI 2024] Invitation to serve as Reviewer', parent_group='Reviewers/Invited',
                                 status=['bounce', 'processed', 'dropped', 'error', 'blocked', 'deferred'])


# save to file:
header_invitations = ['email', 'status', 'name', 'invitation link']
with open('reviewers_failed.csv', 'w') as f:
    w = csv.DictWriter(f, header_invitations)
    w.writeheader()
    for i in range(len(mes_failed)):
        recip = mes_failed[i]['content']['to']
        stat = mes_failed[i]['status']
        name = mes_failed[i]['content']['text'].split('Dear ')[1].split(',\n\n')[0]
        url = mes_failed[i]['content']['text'].split('following link:\n\n')[1].split('\n\nUAI 2024')[0]
        row = {'email': recip, 'status': stat, 'name': name, 'invitation link': url}
        w.writerow(row)


# analyze:
mes_success = client.get_messages(subject='[UAI 2024] Invitation to serve as Reviewer', parent_group='Reviewers/Invited',
                                 status=['delivered'], limit=5000)
mes_failed = client.get_messages(subject='[UAI 2024] Invitation to serve as Reviewer', parent_group='Reviewers/Invited',
                                 status=['bounce', 'processed', 'dropped', 'error', 'blocked', 'deferred'])
with_prof = []
for i in range(len(mes_failed)):
    email = mes_failed[i]['content']['to']
    try:
        prof = client.get_profile(email)
        stat = mes_failed[i]['status']
        name = mes_failed[i]['content']['text'].split('Dear ')[1].split(',\n\n')[0]
        with_prof.append({'email': email, 'status': stat, 'name': name})
    except openreview.OpenReviewException:
        pass

header_invitations = ['email', 'status', 'name']
with open('preferred.csv', 'w') as f:
    w = csv.DictWriter(f, header_invitations)
    w.writeheader()
    for entry in with_prof:
        w.writerow(entry)

for entry in with_prof:
    prof = client.get_profile(entry['email'])
    print(prof.id)


invited_id = '/Reviewers/Invited'
rev_id = '/Reviewers'
declined_id = '/Declined'

acc_rev = list(openreview.tools.iterget_groups(client, id=venue_id+rev_id))[0]
dec_rev = list(openreview.tools.iterget_groups(client, id=venue_id+rev_id+declined_id))[0]
reviewer_names = set()
for entry in acc_rev.members:
    try:
        name = client.get_profile(entry).content['names'][0]['fullname']
        reviewer_names.add(name)
    except openreview.OpenReviewException:
        pass

for entry in dec_rev.members:
    try:
        name = client.get_profile(entry).content['names'][0]['fullname']
        reviewer_names.add(name)
    except openreview.OpenReviewException:
        pass


new_with_prof = []
for entry in with_prof:
    if entry['name'] not in reviewer_names:
        new_with_prof.append(entry)
    else:
        print(entry)
print(set(with_prof).difference(new_with_prof))

header_invitations = ['email', 'status', 'name']
with open('preferred.csv', 'w') as f:
    w = csv.DictWriter(f, header_invitations)
    w.writeheader()
    for entry in new_with_prof:
        w.writerow(entry)


""" Checking if the reviewers who declined the invite have suggested other reviewers: some people suggest 
alternative reviewers in comments"""
decline_messages_rev = list(client.get_all_notes(invitation='auai.org/UAI/2024/Conference/Reviewers/-/Recruitment'))
with open('reviewer_comments_new.csv', 'w') as f:
    headers = ['reviewer', 'comment']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for entry in decline_messages_rev:
        try:
            comment = entry.content['comment']['value']
            if '2' in comment or '3' in comment or 'papers' in comment or 'load' in comment:
                w.writerow({'reviewer': entry.content['user']['value'], 'comment': comment})
        except KeyError:
            pass


""" Set max load for reviewers or ACs: the automatic paper matching respects this maximum number of papers"""

max_load = 2
# for ACs, change Reviewers to Area_Chairs everywhere:
client.post_edge(openreview.api.Edge(
    invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
    head='<your_venue_id>/Reviewers',
    tail='<the_id_of_the_reviewer>',
    signatures=[venue_id + '/Program_Chairs'],
    weight=max_load
))

# Check the assigned max load:
edges = client.get_edges(
    invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
    tail='<the_id_of_the_reviewer>'
)
custom_max_papers_edge = edges[0]
