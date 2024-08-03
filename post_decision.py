import openreview
from credentials import credentials
import csv

""" 
    Connecting to OpenReview  
"""

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=credentials['user'],
                                         password=credentials['pw'])
venue_id = 'auai.org/UAI/2024/Conference'
venue_group = client.get_group(venue_id)
submission_name = venue_group.content['submission_name']['value']

""" Get all submissions """
# submissions = client.get_all_notes(invitation=f'{venue_id}/-/{submission_name}')

""" Get all accepted submissions """
accepted_sub = client.get_all_notes(content={'venueid': venue_id})


""" Get author info from accepted papers """
with open('accepted_papers.csv', 'w') as f:
    headers = ['paper number', 'title', 'authors', 'author info', 'keywords', 'abstract']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for sub in accepted_sub:
        num = sub.number
        title = sub.content['title']['value']
        keywords = sub.content['keywords']['value']
        abstract = sub.content['abstract']['value']
        author_ids = sub.content['authorids']['value']
        # _profiles = openreview.tools.get_profiles(client, sub.content['authorids']['value'])
        first_author = True
        for aid in author_ids:
            profile = openreview.tools.get_profile(client, aid)
            author, author_info = profile.get_preferred_name(pretty=True), profile.content.get('history', [{}])[0]
            if first_author:
                first_author = False
                w.writerow({'paper number': num, 'title': title, 'authors': author, 'author info': author_info,
                        'keywords': keywords, 'abstract': abstract})
            else:
                w.writerow({'paper number': '', 'title': '', 'authors': author, 'author info': author_info,
                            'keywords': '', 'abstract': ''})
        w.writerow({'paper number': '-----', 'title': '------', 'authors': '-----', 'author info': '-----',
                    'keywords': '-----', 'abstract': '------'})

for sub in accepted_sub[:10]:
    print(sub.number, sub.content['title']['value'])
    author_profiles = openreview.tools.get_profiles(client, sub.content['authorids']['value'])
    for author_profile in author_profiles:
        print(author_profile.get_preferred_name(pretty=True), author_profile.content.get('history', [{}])[0])
    print()


""" Get the list of ACs """
ac_id = '/Area_Chairs'

acc_ac = list(openreview.tools.iterget_groups(client, id=venue_id+ac_id))[0]
with open('ac_list.csv', 'w') as f:
    headers = ['lastname', 'firstname', 'fullname', 'affiliation', 'homepage']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for entry in acc_ac.members:
        cnt = client.get_profile(entry).content
        names = cnt['names'][0]
        if 'homepage' in cnt.keys():
            w.writerow({'lastname': names['last'], 'firstname': names['first'], 'fullname': names['fullname'],
                'affiliation': cnt['history'], 'homepage': cnt['homepage']})
        else:
            w.writerow({'lastname': names['last'], 'firstname': names['first'], 'fullname': names['fullname'],
                        'affiliation': cnt['history'], 'homepage': ''})


with open('ac_list2.csv', 'w') as f:
    headers = ['lastname', 'firstname', 'fullname', 'institute', 'position', 'start date', 'end date', 'homepage']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for entry in acc_ac.members:
        cnt = client.get_profile(entry).content
        names = cnt['names'][0]
        affiliation = cnt['history'][0]
        if 'homepage' in cnt.keys():
            w.writerow({'lastname': names['last'], 'firstname': names['first'], 'fullname': names['fullname'],
                    'institute': affiliation['institution']['name'], 'position': affiliation['position'],
                    'start date': affiliation['start'], 'end date': affiliation['end'],
                    'homepage': cnt['homepage']})
        else:
            w.writerow({'lastname': names['last'], 'firstname': names['first'], 'fullname': names['fullname'],
                    'institute': affiliation['institution']['name'], 'position': affiliation['position'],
                    'start date': affiliation['start'], 'end date': affiliation['end'], 'homepage': ''})


""" Get all accepted submissions """
accepted_sub = client.get_all_notes(content={'venueid': venue_id})


""" Get info from accepted papers """
with open('paper_info.csv', 'w') as f:
    headers = ['title', 'authors', 'authorids', 'keywords', 'abstract', 'pdf', 'venue']
    w = csv.DictWriter(f, ['number'] + headers)
    w.writeheader()
    for sub in accepted_sub:
        row = {key: sub.content[key]['value'] for key in headers}
        row['number'] = sub.number
        w.writerow(row)

""" Get author info from accepted papers """
with open('author_info_new.csv', 'w') as f:
    headers = ['author_id', 'author_name', 'paper_number', 'paper_title', 'author_affiliation']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for sub in accepted_sub:
        authors = sub.content['authorids']['value']
        for auth in authors:
            profile = openreview.tools.get_profile(client, auth)
            author, author_info = profile.get_preferred_name(pretty=True), profile.content.get('history', [{}])[0]
            w.writerow({'author_id': auth, 'author_name': author,
                        'paper_number': sub.number, 'paper_title': sub.content['title']['value'],
                        'author_affiliation': author_info})


""" Get author emails who have not registered for the conference """
all_mes = client.get_messages(subject='[UAI 2024] Camera ready instructions', parent_group='Authors/Accepted')
not_reg_sub = client.get_all_notes(content={'venueid': venue_id},
                                   number=['<the submission numbers>'])
with open('author_emails_registration.csv', 'w') as f:
    headers = ['paper_number', 'paper_title', 'authors', 'author_emails']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for sub in not_reg_sub:
        auths = sub.content['authors']['value']
        emails = []
        for auth in auths:
            for mes in all_mes:
                if mes['content']['text'].split(',')[0].split('Dear ')[1] == auth:
                    emails.append(mes['content']['to'])
                    break
        w.writerow({'paper_number': sub.number, 'paper_title': sub.content['title']['value'],
                    'authors': auths, 'author_emails': emails})




