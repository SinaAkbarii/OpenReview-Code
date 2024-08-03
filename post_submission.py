import openreview
from credentials import credentials
from utils import find_word_in_pdf
import csv
import os
from utils import send_email

""" 
    Connecting to OpenReview  
"""

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=credentials['user'],
                                         password=credentials['pw'])
venue_id = 'auai.org/UAI/2024/Conference'
venue_group = client.get_group(venue_id)


""" 
    Extracting the list of submissions and their abstracts for the integrity chairs
"""

submission_name = venue_group.content['submission_name']['value']
withdrawn_name = venue_group.content['withdrawn_venue_id']['value'].split('/')[-1]
deskreject_name = venue_group.content['desk_rejected_venue_id']['value'].split('/')[-1]

submissions = client.get_all_notes(invitation=f'{venue_id}/-/{submission_name}')
withdrawn_submissions = client.get_all_notes(invitation=f'{venue_id}/-/{withdrawn_name}')
deskreject_submissions = client.get_all_notes(invitation=f'{venue_id}/-/{deskreject_name}')

deleted_ids = [sub.id for sub in set(deskreject_submissions).union(withdrawn_submissions)]
j = 0
with open('all_submissions.csv', 'w') as f:
    headers = ['title', 'authors', 'authorids', 'keywords', 'abstract']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for sub in submissions:
        if sub.id in deleted_ids:
            print(j)
            j += 1
            print(sub.content['title']['value'])
            continue
        w.writerow({k: sub.content[k]['value'] for k in headers})

"""
    Download all submissions
"""

for note in submissions:
    f = client.get_attachment(note.id, 'pdf')
    with open(f'./all_submissions/paper{note.number}.pdf', 'wb') as op:
        op.write(f)

"""
    Check page limit
"""

# Replace 'your_pdf_file.pdf' with the actual path to your PDF file
pdf_file_path = './all_submissions/'
target_word = 'references'

files = os.listdir('./all_submissions/')
for file in files:
    num_page, text_before = find_word_in_pdf(pdf_file_path + file, target_word)
    if num_page is None:
        num_page, text_before = find_word_in_pdf(pdf_file_path + file, 'bibliography')
    if num_page is None:
        print(f'{file}, no occurrence!')
    elif num_page > 9:
        print(f'{file}, page={num_page}')
    elif num_page == 9 and text_before:
        print(f'{file}, page=9, text before!')

"""
    desk reject notes
"""

desk_rejected_venue_id = client.get_group(venue_id).content['desk_rejected_venue_id']['value']
submission_name = client.get_group(venue_id).content['submission_name']['value']
submissions = client.get_all_notes(content={'venueid': venue_id + '/' + submission_name})
sub0 = submissions[0]
notes = client.get_all_notes(
    forum='<forum_id>'
)
client.post_note_edit(
    invitation=venue_id + '/-/Edit',
    readers=[venue_id],
    writers=[venue_id],
    signatures=[venue_id],
    note=openreview.api.Note(
        id='<submission_id>',
        readers=[
            venue_id + '/Program_Chairs', venue_id + '/Submission<number>/Authors'
        ]
    )
)


"""
    Checking if there is a desk-reject-reverted paper
"""
submission_name = client.get_group(venue_id).content['submission_name']['value']
submissions = client.get_all_notes(content={'venueid': venue_id + '/' + submission_name})
for sub in submissions:
    notes = client.get_all_notes(
        forum=sub.id
    )
    if len(notes) > 1:
        print(sub.id)




