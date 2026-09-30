from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID


class FakeResponse:
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class FakeAuth:
    def __init__(self):
        self.sign_up_response = None
        self.sign_in_response = None
        self.get_user_response = None

    def sign_up(self, payload):
        return self.sign_up_response

    def sign_in_with_password(self, payload):
        return self.sign_in_response

    def get_user(self, jwt):
        return self.get_user_response


class FakePostgrest:
    def __init__(self):
        self.access_token = None

    def auth(self, access_token):
        self.access_token = access_token


class FakeSupabaseClient:
    def __init__(self, tables=None):
        self.tables = {
            table_name: deepcopy(rows)
            for table_name, rows in (tables or {}).items()
        }
        self.operations = []
        self.auth = FakeAuth()
        self.postgrest = FakePostgrest()
        self._next_id = 1

    def table(self, table_name):
        return FakeQuery(self, table_name)

    def seed(self, table_name, rows):
        self.tables[table_name] = deepcopy(rows)

    def _generate_id(self):
        value = str(UUID(int=self._next_id))
        self._next_id += 1
        return value


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.operation = None
        self.payload = None
        self.filters = []
        self.order_field = None
        self.order_desc = False
        self.limit_value = None

    def select(self, columns="*"):
        if self.operation is None:
            self.operation = "select"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = deepcopy(payload)
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = deepcopy(payload)
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def lte(self, field, value):
        self.filters.append(("lte", field, value))
        return self

    def order(self, field, desc=False):
        self.order_field = field
        self.order_desc = desc
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])

        if self.operation == "insert":
            inserted_rows = self.payload
            if not isinstance(inserted_rows, list):
                inserted_rows = [inserted_rows]

            result = []
            for payload in inserted_rows:
                row = deepcopy(payload)
                row.setdefault("id", self.client._generate_id())
                now = datetime.now(timezone.utc).isoformat()
                row.setdefault("created_at", now)
                row.setdefault("updated_at", now)
                rows.append(row)
                result.append(deepcopy(row))
        elif self.operation == "update":
            result = []
            for row in rows:
                if self._matches(row):
                    row.update(deepcopy(self.payload))
                    result.append(deepcopy(row))
        elif self.operation == "delete":
            result = []
            remaining = []
            for row in rows:
                if self._matches(row):
                    result.append(deepcopy(row))
                else:
                    remaining.append(row)
            self.client.tables[self.table_name] = remaining
        else:
            result = [deepcopy(row) for row in rows if self._matches(row)]

        if self.order_field is not None:
            result.sort(
                key=lambda row: row.get(self.order_field),
                reverse=self.order_desc
            )

        if self.limit_value is not None:
            result = result[:self.limit_value]

        operation = {
            "table": self.table_name,
            "operation": self.operation,
            "payload": deepcopy(self.payload),
            "filters": deepcopy(self.filters),
            "result": deepcopy(result),
        }
        self.client.operations.append(operation)

        return FakeResponse(data=result, count=len(result))

    def _matches(self, row):
        for operator, field, value in self.filters:
            row_value = row.get(field)
            if operator == "eq" and row_value != value:
                return False
            if operator == "lte" and self._compare(row_value, value) > 0:
                return False
        return True

    @staticmethod
    def _compare(left, right):
        if isinstance(left, str) and isinstance(right, str):
            try:
                left = datetime.fromisoformat(left)
                right = datetime.fromisoformat(right)
            except ValueError:
                pass

        if left < right:
            return -1
        if left > right:
            return 1
        return 0
