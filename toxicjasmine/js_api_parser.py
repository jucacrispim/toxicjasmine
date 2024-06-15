# -*- coding: utf-8 -*-


class Result():
    def __init__(
            self,
            status=None,
            full_name=None,
            failed_expectations=None,
            deprecation_warnings=None,
            runnable_id=None,
            description=None,
            pending_reason=None
    ):
        if failed_expectations is None:
            failed_expectations = {}

        self._status = status
        self._full_name = full_name
        self._failed_expectations = failed_expectations
        self._deprecation_warnings = deprecation_warnings
        self._runnable_id = runnable_id
        self._description = description
        self._pending_reason = pending_reason

    @property
    def status(self):
        return self._status

    @property
    def full_name(self):
        return self._full_name

    @property
    def failed_expectations(self):
        return self._failed_expectations

    @property
    def deprecation_warnings(self):
        return self._deprecation_warnings

    @property
    def runnable_id(self):
        return self._runnable_id

    @property
    def description(self):
        return self._description

    @property
    def pending_reason(self):
        return self._pending_reason


class ResultList(list):

    def add_result(self, result):
        self.append(Result(**result))

    def passed(self):
        return self._filter_status('passed')

    def failed(self):
        return self._filter_status('failed')

    def pending(self):
        return self._filter_status('pending')

    def enabled(self):
        return [result for result in self if result.status != 'disabled']

    def _filter_status(self, status):
        return [result for result in self if result.status == status]

    def __add__(self, other):
        return ResultList(list.__add__(self, other))


class Parser(object):
    RESULT_FIELDS = {
        'status': 'status',
        'fullName': 'full_name',
        'failedExpectations': 'failed_expectations',
        'deprecationWarnings': 'deprecation_warnings',
        'id': 'runnable_id',
        'description': 'description',
        'pendingReason': 'pending_reason'
    }

    def parse(self, items):
        result_list = ResultList()
        for item in self._filter_fields(items):
            result_list.add_result(item)
        return result_list

    def _filter_fields(self, raw_items):
        filtered_items = []
        for item in raw_items:
            filtered_items.append(dict((
                (self._to_snake_case(k), v)
                for k, v in item.items()
                if k in self.RESULT_FIELDS.keys()
            )))
        return filtered_items

    def _to_snake_case(self, key):
        return self.RESULT_FIELDS[key]
