import openreview
from credentials import credentials
import csv
from utils import send_email

""" 
    Connecting to OpenReview  
"""

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=credentials['user'],
                                         password=credentials['pw'])
venue_id = 'auai.org/UAI/2024/Conference'
venue_group = client.get_group(venue_id)


""" Getting missing reviews """
venue_group = client.get_group(venue_id)
submission_name = venue_group.content['submission_name']['value']
review_name = venue_group.content['review_name']['value']
submissions = client.get_all_notes(invitation=f'{venue_id}/-/{submission_name}', details='replies')
ac_invitation = venue_id + '/Area_Chairs/-/Assignment'
rev_invitation = venue_id + '/Reviewers/-/Assignment'
# for s in submissions:
#     # get the reviews:
#     s_reviews = [openreview.api.Note.from_json(reply) for reply in s.details['replies'] if
#                  f'{venue_id}/{submission_name}{s.number}/-/{review_name}' in reply['invitations']]
#     # if there are less than three reviews submitted, note the submission, and get its AC:
#     if len(s_reviews) < 3:
#         edges = client.get_all_edges(invitation=ac_invitation, head=s.id)
#         if len(edges) > 0:
#             print(edges[0].tail)

submission_name = venue_group.content['submission_name']['value']
withdrawn_name = venue_group.content['withdrawn_venue_id']['value'].split('/')[-1]
deskreject_name = venue_group.content['desk_rejected_venue_id']['value'].split('/')[-1]
submissions = client.get_all_notes(invitation=f'{venue_id}/-/{submission_name}')
withdrawn_submissions = client.get_all_notes(invitation=f'{venue_id}/-/{withdrawn_name}')
deskreject_submissions = client.get_all_notes(invitation=f'{venue_id}/-/{deskreject_name}')

deleted_ids = [sub.id for sub in set(deskreject_submissions).union(withdrawn_submissions)]

with open('missing_reviews.csv', 'w') as f:
    headers = ['corresponding area chair', '# submitted reviews', 'paper #', 'title', 'missing_rev',
               'missing_rev_anonym']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for s in submissions:
        if s.id in deleted_ids:
            continue
        # get the reviews:
        # s_reviews = [openreview.api.Note.from_json(reply) for reply in s.details['replies'] if
        #              f'{venue_id}/{submission_name}{s.number}/-/{review_name}' in reply['invitations']]
        s_reviewers_submitted = [reply['signatures'][0] for reply in s.details['replies'] if
                     f'{venue_id}/{submission_name}{s.number}/-/{review_name}' in reply['invitations']]
        # if there are less than three reviews submitted, note the submission, and get its AC:
        if len(s_reviewers_submitted) < 3:
            edges = client.get_all_edges(invitation=ac_invitation, head=s.id)
            if len(edges) > 0:
                revs = client.get_group(f'{venue_id}/{submission_name}{s.number}/Reviewers').members
                revs_anonym = client.get_group(f'{venue_id}/{submission_name}{s.number}/Reviewers').anon_members
                revs_not_submitted_ind = [i for i, rev in enumerate(revs_anonym) if rev not in s_reviewers_submitted]
                for ind in revs_not_submitted_ind:
                    w.writerow({'corresponding area chair': edges[0].tail,
                                '# submitted reviews': len(s_reviewers_submitted), 'paper #': s.number,
                                'title': s.content['title']['value'], 'missing_rev': revs[ind],
                                'missing_rev_anonym': revs_anonym[ind]})

import pandas as pd
file_path = 'missing_reviews.csv'
data = pd.read_csv(file_path)
grouped_data = data.groupby('missing_rev')

mes_path = 'message_missing_revs.txt'
with open(mes_path, 'r') as file:
    message_missing = file.read()
# Iterate over each group and send emails to missing reviews
for missing_rev, group in grouped_data:
    print(f"Entries for missing reviewer: {missing_rev}")
    mes = message_missing + '\n\n' + group[['paper #', 'title']].to_string(index=False, header=False)
    # print(mes)
    send_email(client, recipients=[missing_rev],
               title='[UAI 2024] Urgent: Required Action Regarding Missing Reviews', message=mes)
    # break
