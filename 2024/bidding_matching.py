import openreview
from credentials import credentials
import csv
from utils import send_email
import datetime

""" 
    Connecting to OpenReview  
"""

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=credentials['user'],
                                         password=credentials['pw'])
venue_id = 'auai.org/UAI/2024/Conference'
venue_group = client.get_group(venue_id)


"""
    Set max load for reviewers from a file:
"""
revs = []
with open('revs_reduced.csv', 'r') as f:
    # Create a CSV reader object
    csv_reader = csv.reader(f)
    # Access headers using fieldnames attribute
    headers = next(csv_reader)
    # Iterate through each row in the CSV file
    for row in csv_reader:
        try:
            prof = client.get_profile(row[2]).id
            revs.append({'profile': prof, 'load': int(row[3])})
        except openreview.openreview.OpenReviewException:
            print(row)
            continue

venue_id = 'auai.org/UAI/2024/Conference'

for rev in revs:
    # print(rev)
    client.post_edge(openreview.api.Edge(
        invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
        head=venue_id + '/Reviewers',
        tail=rev['profile'],
        signatures=[venue_id + '/Program_Chairs'],
        weight=rev['load']
    ))

# The procedure for ACs is the same:
client.post_edge(openreview.api.Edge(
    invitation=venue_id + '/Area_Chairs/-/Custom_Max_Papers',
    head=venue_id + '/Area_Chairs',
    tail='<AC_iD>',
    signatures=[venue_id + '/Program_Chairs'],
    weight=0
))

#Check the already assigned max load:
edges = client.get_edges(
    invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
    tail='<reviewer_id>'
)[0]

# Change the max load:
edges.weight = 5
client.post_edge(edges)

"""
    Reviewers without profiles on OpenReview:
"""
revs = client.get_group(venue_id + '/Reviewers')

rev_no_id = [rev for rev in revs.members if '@' in rev]
with open('rev_no_profile.csv', 'w') as f:
    headers = ['email']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for rev in rev_no_id:
        w.writerow({'email': rev})

new_ids = []
with open('rev_no_profile.csv', 'r') as f:
    csv_reader = csv.reader(f)
    # Access headers using fieldnames attribute
    headers = next(csv_reader)
    # Iterate through each row in the CSV file
    for row in csv_reader:
        try:
            prof = client.get_profile(row[0]).id
            new_ids.append(prof)
        except openreview.openreview.OpenReviewException:
            print(row)
            continue

"""
    Get reviewer conflicts
"""
edges = client.get_edges(
    invitation=venue_id + '/Reviewers/-/Conflict',
    tail='<reviewer_id>'
)

"""
    Get Reviewer Bids
"""

def get_bids(rev_id, client, ac=False):
    """
    :param rev_id: OpenReview ~ profile
    :param client: OpenReview Client object
    :param ac: if True, the search is done in Area Chairs Group. If False, the reviewer bids are returned.
    :return: The submission notes a reviewer has bidden on.
    """
    venue_id = 'auai.org/UAI/2024/Conference'
    venue_group = client.get_group(venue_id)
    if ac:  # getting bids for area chairs
        bid_id = venue_group.content['area_chairs_id']['value']
    else:  # getting bids for reviewers:
        bid_id = venue_group.content['reviewers_id']['value']
    bid_id += '/-/' + venue_group.content['bid_name']['value']
    return client.get_edges(
        invitation=bid_id,
        tail=rev_id
    )


""" Get the reviewers that have placed a low number of bids:"""


def get_low_bid(client, max_bid=0, ac=False):
    venue_id = 'auai.org/UAI/2024/Conference'
    venue_group = client.get_group(venue_id)
    if ac:
        rev_id = venue_group.content['area_chairs_id']['value']
    else:
        rev_id = venue_group.content['reviewers_id']['value']
    return [rev for rev in client.get_group(id=rev_id).members if len(get_bids(rev, client, ac)) <= max_bid]


revs_zero_bid = get_low_bid(client, max_bid=0, ac=False)
acs_zero_bid = get_low_bid(client, max_bid=0, ac=True)

ac_mes_path = './mes_acs.txt'
rev_mes_path = './mes_revs.txt'
with open(ac_mes_path, 'r') as file:
    message_acs = file.read()
with open(rev_mes_path, 'r') as file:
    message_revs = file.read()
send_email(client, recipients=acs_zero_bid, title='[UAI 2024] Reminder: paper bidding', message=message_acs)
send_email(client, recipients=revs_zero_bid, title='[UAI 2024] Reminder: paper bidding', message=message_revs)


""" You may want to assign no papers to those who have not placed bids: """
for rev in revs_zero_bid:
    try:
        edges = client.get_edges(
            invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
            tail=rev
        )[0]
        print(f'load of reviewer {rev} reduced from {edges.weight} to 0')
        edges.weight = 0
        client.post_edge(edges)
    except IndexError:
        client.post_edge(openreview.api.Edge(
            invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
            head=venue_id + '/Reviewers',
            tail=rev,
            signatures=[venue_id + '/Program_Chairs'],
            weight=0
        ))

with open('reviewer_no_bid.csv', 'w') as f:
    headers = ['id']
    w = csv.DictWriter(f, headers)
    w.writeheader()
    for rev in revs_zero_bid:
        w.writerow({'id': rev})


"""
    Send emails to those who have not placed bids yet
"""

revs_zero_bid_new = []
revs_zero_bid_to_delete = []
for rev in revs_zero_bid:
    if len(get_bids(rev, client, ac=False)) == 0:
        revs_zero_bid_new.append(rev)
    else:
        revs_zero_bid_to_delete.append(rev)

""" reset the max load for those who have placed bids"""
for rev in revs_zero_bid_to_delete:
    edges = client.get_edges(
        invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
        tail=rev
    )[0]
    edges.weight = 6
    client.post_edge(edges)

""" send an email to the rest """
ac_mes_path = './mes_ac_nobids.txt'
rev_mes_path = './mes_rev_nobids.txt'
with open(ac_mes_path, 'r') as file:
    message_acs = file.read()
with open(rev_mes_path, 'r') as file:
    message_revs = file.read()
send_email(client, recipients=acs_zero_bid, title='[UAI 2024] Last reminder: paper bidding', message=message_acs)
send_email(client, recipients=['~Sina_Akbari1'], title='[UAI 2024] Last reminder: paper bidding', message=message_revs)

""" Restore reviewer max loads to 6"""
with open('reviewer_no_bid.csv', 'r') as f:
    csv_reader = csv.reader(f)
    # Access headers using fieldnames attribute
    headers = next(csv_reader)
    # Iterate through each row in the CSV file
    for rev in csv_reader:
        edges = client.get_edges(
            invitation=venue_id + '/Reviewers/-/Custom_Max_Papers',
            tail=rev
        )[0]
        if edges.weight == 0:
            edges.weight = 6
            client.post_edge(edges)

"""
    Get all papers assigned to a reviewer
"""
venue_id = 'auai.org/UAI/2024/Conference'
invitation = venue_id + '/Reviewers/-/Assignment'
tail = '<reviewer_id>'
edges = client.get_all_edges(invitation=invitation, tail=tail)
# remove the first assignment:
edge = edges[0]
edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
client.post_edge(edge)
