import pickle
import os
import re

from nose.tools import with_setup
from sqlalchemy.exc import OperationalError
from testil import Config, assert_raises, eq, tempdir

from corehq.apps.tzmigration.timezonemigration import FormJsonDiff as JsonDiff

from ..statedb import (
    Counts,
    ResumeError,
    StateDB,
    _get_state_db_filepath,
    delete_state_db,
    diff_doc_id_idx,
    init_state_db,
    open_state_db,
)
from .. import statedb as mod


def setup_module():
    global _tmp, state_dir
    _tmp = tempdir()
    state_dir = _tmp.__enter__()


def teardown_module():
    _tmp.__exit__(None, None, None)


def init_db(name="test", memory=True):
    if memory:
        return StateDB.init(":memory:")
    return init_state_db(name, state_dir)


def delete_db(name="test"):
    delete_state_db(name, state_dir)


@with_setup(teardown=delete_db)
def test_db_unique_id():
    with init_db(memory=False) as db:
        uid = db.unique_id
        assert re.search(r"\d{8}-\d{6}.\d{6}", uid), uid

    with init_db(memory=False) as db:
        eq(db.unique_id, uid)

    delete_db()
    with init_db(memory=False) as db:
        assert db.unique_id != uid, uid


@with_setup(teardown=delete_db)
def test_open_state_db():
    with open_state_db("test", state_dir) as db:
        with assert_raises(OperationalError):
            db.unique_id
        with assert_raises(OperationalError):
            db.get_diff_stats()
        with assert_raises(OperationalError):
            db.set("key", 1)
    assert not os.path.exists(_get_state_db_filepath("test", state_dir))
    with init_db(memory=False) as db:
        uid = db.unique_id
        eq(db.get("key"), None)
        db.set("key", 2)
    with open_state_db("test", state_dir) as db:
        eq(db.unique_id, uid)
        eq(db.get_diff_stats(), {})
        eq(db.get("key"), 2)
        with assert_raises(OperationalError):
            db.set("key", 3)


def test_update_cases():
    with init_db() as db:
        result = db.update_cases([
            Config(id="a", total_forms=2, processed_forms=1),
            Config(id="b", total_forms=2, processed_forms=1),
            Config(id="c", total_forms=2, processed_forms=1),
        ])
        eq(sorted(result), [
            ("a", 2, 1),
            ("b", 2, 1),
            ("c", 2, 1),
        ])
        result = db.update_cases([
            Config(id="b", total_forms=1, processed_forms=3),
            Config(id="c", total_forms=3, processed_forms=1),
            Config(id="d", total_forms=2, processed_forms=1),
        ])
        eq(sorted(result), [
            ("b", 2, 4),
            ("c", 3, 2),
            ("d", 2, 1),
        ])


def test_add_processed_forms():
    with init_db() as db:
        db.update_cases([
            Config(id="a", total_forms=2, processed_forms=1),
            Config(id="b", total_forms=2, processed_forms=1),
            Config(id="c", total_forms=4, processed_forms=1),
        ])
        result = db.add_processed_forms({"b": 1, "c": 2, "d": 2})
        eq(sorted(result), [
            ("b", 2, 2),
            ("c", 4, 3),
            ("d", None, None),
        ])


def test_iter_cases_with_unprocessed_forms():
    with init_db() as db:
        db.update_cases([
            Config(id="a", total_forms=2, processed_forms=1),
            Config(id="b", total_forms=2, processed_forms=1),
            Config(id="c", total_forms=4, processed_forms=1),
        ])
        eq(list(db.iter_cases_with_unprocessed_forms()),
            [("a", 2), ("b", 2), ("c", 4)])


def test_get_forms_count():
    with init_db() as db:
        db.update_cases([
            Config(id="a", total_forms=2, processed_forms=1),
            Config(id="b", total_forms=2, processed_forms=3),
        ])
        eq(db.get_forms_count("a"), 2)
        eq(db.get_forms_count("b"), 2)
        eq(db.get_forms_count("c"), 0)


@with_setup(teardown=delete_db)
def test_problem_forms():
    with init_db(memory=False) as db:
        db.add_problem_form("abc")

    with init_db(memory=False) as db:
        db.add_problem_form("def")
        eq(set(db.iter_problem_forms()), {"abc", "def"})


@with_setup(teardown=delete_db)
def test_no_action_case_forms():
    with init_db(memory=False) as db:
        db.add_no_action_case_form("abc")

    with init_db(memory=False) as db:
        eq(db.get_no_action_case_forms(), {"abc"})

        # verify that memoized result is cleared on add
        db.add_no_action_case_form("def")
        eq(db.get_no_action_case_forms(), {"abc", "def"})


def test_duplicate_no_action_case_form():
    with init_db() as db:
        db.add_no_action_case_form("abc")
        db.add_no_action_case_form("abc")  # should not raise


@with_setup(teardown=delete_db)
def test_resume_state():
    with init_db(memory=False) as db:
        with db.pop_resume_state("test", []) as value:
            eq(value, [])
        db.set_resume_state("test", ["abc", "def"])

    with init_db(memory=False) as db, assert_raises(ValueError):
        with db.pop_resume_state("test", []) as value:
            # error in context should not cause state to be lost
            raise ValueError(value)

    with init_db(memory=False) as db:
        with db.pop_resume_state("test", []) as value:
            eq(value, ["abc", "def"])

    # simulate resume without save
    with init_db(memory=False) as db:
        with assert_raises(ResumeError):
            with db.pop_resume_state("test", []):
                pass


def test_replace_case_diffs():
    with init_db() as db:
        case_id = "865413246874321"
        # add old diffs
        db.replace_case_diffs("CommCareCase", case_id, [make_diff(0)])
        db.replace_case_diffs("CommCareCase", "unaffected", [make_diff(1)])
        db.add_diffs("stock state", case_id + "/x/y", [make_diff(2)])
        db.add_diffs("stock state", "unaffected/x/y", [make_diff(3)])
        # add new diffs
        db.replace_case_diffs("CommCareCase", case_id, [make_diff(4)])
        db.add_diffs("stock state", case_id + "/y/z", [make_diff(5)])
        eq(
            {(d.kind, d.doc_id, d.json_diff) for d in db.get_diffs()},
            {(kind, doc_id, make_diff(x)) for kind, doc_id, x in [
                ("CommCareCase", "unaffected", 1),
                ("stock state", "unaffected/x/y", 3),
                ("CommCareCase", case_id, 4),
                ("stock state", case_id + "/y/z", 5),
            ]},
        )


def test_save_form_diffs():
    def doc(name):
        return {"doc_type": "XFormInstance", "_id": "test", "name": name}

    def check_diffs(expect_count):
        diffs = db.get_diffs()
        eq(len(diffs), expect_count, [d.json_diff for d in diffs])

    with init_db() as db:
        db.save_form_diffs(doc("a"), doc("b"))
        db.save_form_diffs(doc("a"), doc("c"))
        check_diffs(2)
        db.save_form_diffs(doc("a"), doc("d"), replace=True)
        check_diffs(1)
        db.save_form_diffs(doc("a"), doc("a"), replace=True)
        check_diffs(0)


def test_counters():
    with init_db() as db:
        db.increment_counter("abc", 1)
        db.add_missing_docs("abc", ["doc1"])
        db.increment_counter("def", 2)
        db.increment_counter("abc", 3)
        db.add_missing_docs("abc", ["doc2", "doc4"])
        eq(db.get_doc_counts(), {
            "abc": Counts(4, 3),
            "def": Counts(2, 0),
        })


def test_diff_doc_id_idx_exists():
    msg = re.compile("index diff_doc_id_idx already exists")
    with init_db() as db, assert_raises(OperationalError, msg=msg):
        diff_doc_id_idx.create(db.engine)


@with_setup(teardown=delete_db)
def test_pickle():
    with init_db(memory=False) as db:
        other = pickle.loads(pickle.dumps(db))
        assert isinstance(other, type(db)), (other, db)
        assert other is not db
        eq(db.unique_id, other.unique_id)


def test_clone_casediff_data_from():
    diffs = [make_diff(i) for i in range(3)]
    try:
        with init_db("main", memory=False) as main:
            uid = main.unique_id
            with init_db("cddb", memory=False) as cddb:
                main.add_problem_form("problem")
                main.save_form_diffs({"doc_type": "XFormInstance", "_id": "form"}, {})
                cddb.add_processed_forms({"case": 1})
                cddb.update_cases([
                    Config(id="case", total_forms=1, processed_forms=1),
                    Config(id="a", total_forms=2, processed_forms=1),
                    Config(id="b", total_forms=2, processed_forms=1),
                    Config(id="c", total_forms=2, processed_forms=1),
                ])
                cddb.add_missing_docs("CommCareCase-couch", ["missing"])
                cddb.replace_case_diffs("CommCareCase", "a", [diffs[0]])
                cddb.replace_case_diffs("CommCareCase-Deleted", "b", [diffs[1]])
                cddb.add_diffs("stock state", "c/ledger", [diffs[2]])
                cddb.increment_counter("CommCareCase", 3)           # case, a, c
                cddb.increment_counter("CommCareCase-Deleted", 1)   # b
                cddb.increment_counter("CommCareCase-couch", 1)     # missing
                main.add_no_action_case_form("no-action")
                main.set_resume_state("FormState", ["form"])
                cddb.set_resume_state("CaseState", ["case"])
            cddb.close()
            main.clone_casediff_data_from(cddb.db_filepath)
        main.close()

        with StateDB.open(main.db_filepath) as db:
            eq(list(db.iter_cases_with_unprocessed_forms()), [("a", 2), ("b", 2), ("c", 2)])
            eq(list(db.iter_problem_forms()), ["problem"])
            eq(db.get_no_action_case_forms(), {"no-action"})
            with db.pop_resume_state("CaseState", "nope") as value:
                eq(value, ["case"])
            with db.pop_resume_state("FormState", "fail") as value:
                eq(value, ["form"])
            eq(db.unique_id, uid)
    finally:
        delete_db("main")
        delete_db("cddb")


def test_clone_casediff_data_from_tables():
    from corehq.apps.tzmigration.planning import (
        PlanningForm,
        PlanningCase,
        PlanningCaseAction,
        PlanningStockReportHelper,
    )
    # Any time a model is added to this list it must be analyzed for usage
    # by the case diff process. StateDB.clone_casediff_data_from() may need
    # to be updated.
    eq(set(mod.Base.metadata.tables), {m.__tablename__ for m in [
        mod.CaseForms,
        mod.Diff,
        mod.KeyValue,
        mod.DocCount,
        mod.MissingDoc,
        mod.NoActionCaseForm,
        mod.ProblemForm,
        # models not used by couch-to-sql migration
        PlanningForm,
        PlanningCase,
        PlanningCaseAction,
        PlanningStockReportHelper,
    ]})


def test_get_set():
    with init_db() as db:
        eq(db.get("key"), None)
        eq(db.get("key", "default"), "default")
        db.set("key", True)
        eq(db.get("key"), True)


def make_diff(id):
    return JsonDiff("type", "path/%s" % id, "old%s" % id, "new%s" % id)
