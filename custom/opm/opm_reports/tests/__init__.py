from datetime import datetime
import os, json

from django.http import HttpRequest
from django.test import TestCase

from fluff.management.commands.ptop_fast_reindex_fluff import FluffPtopReindexer

from corehq.apps.users.models import WebUser
from corehq.apps.users.models import CommCareUser, CommCareCase
from dimagi.utils.couch.database import get_db
from dimagi.utils.modules import to_function

from ..constants import DOMAIN
from ..beneficiary import Beneficiary
from ..reports import (BeneficiaryPaymentReport, IncentivePaymentReport,
    get_report)
from ..models import (OpmUserFluff, OpmCaseFluffPillow,
    OpmUserFluffPillow, OpmFormFluffPillow)

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
test_data_location = os.path.join(DIR_PATH, 'opm_test.json')
test_month_year = (8, 2013)

fixtures_loaded = False


class OPMTestBase(object):

    def load_fixtures(self):
        print "loading test data"
        self.db = get_db()
        with open(test_data_location) as f:
            docs = json.loads(f.read())
        for doc in docs:
            self.db.save_doc(doc)

    def reindex_fluff(self, pillow):
        flufftop = FluffPtopReindexer()
        dotpath = '.'.join([OpmUserFluff.__module__, pillow.__name__])
        print dotpath
        flufftop.pillow_class = to_function(dotpath)
        flufftop.domain = DOMAIN
        flufftop.resume = False
        flufftop.bulk = False
        flufftop.db = flufftop.doc_class.get_db()
        flufftop.runfile = None
        flufftop.start_num = 0
        flufftop.chunk_size = 500
        flufftop.pillow = flufftop.pillow_class()
        for i, row in enumerate(flufftop.full_couch_view_iter()):
            print "\tProcessing item %s (%d)" % (row['id'], i)
            flufftop.process_row(row, i)

    def setUp(self):
        global fixtures_loaded
        if not fixtures_loaded:
            fixtures_loaded = True
            self.load_fixtures()
            for pillow in [OpmCaseFluffPillow, OpmUserFluffPillow, OpmFormFluffPillow]:
                self.reindex_fluff(pillow)

    def test_all_results(self):
        pass


class TestBeneficiary(OPMTestBase, TestCase):
    ReportClass = BeneficiaryPaymentReport
    
    def get_rows(self):
        return CommCareCase.get_all_cases('opm', include_docs=True)


class TestIncentive(OPMTestBase, TestCase):
    ReportClass = IncentivePaymentReport

    def get_rows(self):
        return CommCareUser.by_domain('opm')
