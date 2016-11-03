#!/usr/bin/env python
import random
import datetime
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User

from jobs.models import Company, Branch, Contact, Job
from references.models import PayStructure, MYOB, Status

def _test():
    print 1

if __name__ == "__main__":
    _test()

DEFAULT_PRICES = [15.5, 17.2, 20.0, 25.5, 30.0, 50.0, 100.0]
PLAN_PRICES = [25.5, 12.0, 30.0, 15.5, 10.0, 0, 0, 0, 0, 10, 15.0, 21.0, 18.5, 0, 0, 0]
DEFAULT_SQUARE = ['A3', 'A4', '', '', '', 'X1' , 'X2']

def jobs( count=None, IsTrace=None ):
    if not count:
        count = 1
    companies = [ x for x in Company.objects.all().distinct() ]
    user = User.objects.get(id=1)

    n = 0

    while 1:
        if n >= count:
            break
        company = random.choice(companies)

        branches = [ x for x in Branch.objects.filter(company=company.id).distinct() ]
        if not branches:
            continue
        branch = random.choice(branches)

        contacts = [ x for x in Contact.objects.filter(branch=branch.id).distinct() ]
        if not contacts:
            continue
        contact = random.choice(contacts)

        pays = [ x for x in PayStructure.objects.all().distinct() ]
        pay = random.choice(pays)

        myobs = [ x for x in MYOB.objects.all().distinct() ]
        myob = random.choice(myobs)

        statuses = [ x for x in Status.objects.all().distinct() ]
        status = random.choice(statuses)

        title = "JOB %s: %s-%s-%s-%s-%s-%s" % (n, company.id, branch.title, contact.id, pay.id, myob.id, status.title)
        #print title
        n += 1

        job = Job()
        job.company = company
        job.branch = branch
        job.contact = contact
        job.status = status
        job.user = user
        job.title = title
        job.type = random.randint(0,4)
        job.code = 'SPEED-TEST'
        job.received = datetime.datetime.now()
        job.property = random.randrange(0, 10000000, 1000)
        job.square = random.choice(DEFAULT_SQUARE)
        default = random.choice(DEFAULT_PRICES)
        job.default = str(default)
        price = random.choice(PLAN_PRICES)
        job.price = str(price)
        calculated = default > price and default - price or price - default or 0
        calculated = calculated and (random.choice([1, 2, 0, -1, -2]) * 10 + calculated) or 0
        job.calculated = calculated > 0 and str(calculated) or 0
        job.runtime = random.randrange(0, 480, 20)
        job.IsAmendment = random.choice([0, 1, 0, 1, 0, 1])
        job.IsArchive = random.choice([0, 0, 0, 1])

        try:
            job.save()
        except Exception, msg:
            transaction.rollback_unless_managed()
            print "-> exception: %s" % str(msg)
            break

        if IsTrace:
            print "-> %s" % repr(job)

        if n%10 == 0:
            transaction.commit_unless_managed()
            if IsTrace:
                print "-> commit"
            elif n%100 == 0:
                print "-> %s records" % n

