PYTHON ?= python
.PHONY: setup demo test e2e migrate stop backup restore
setup:
	$(PYTHON) -m pip install -r requirements.lock
	cd frontend && pnpm install --frozen-lockfile
demo:
	$(PYTHON) scripts/manage.py build
	$(PYTHON) scripts/manage.py start
test:
	$(PYTHON) scripts/manage.py test
e2e:
	$(PYTHON) scripts/manage.py e2e
migrate:
	$(PYTHON) scripts/manage.py migrate
stop:
	$(PYTHON) scripts/manage.py stop
backup:
	$(PYTHON) scripts/manage.py backup $(DEST)
restore:
	$(PYTHON) scripts/manage.py restore $(SOURCE) $(DEST)
