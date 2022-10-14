# Clean repository.
clean:
	rm -rf __pycache__
	rm -rf tests/__pycache__
	rm -rf dist/
	rm -rf build/
	rm -rf *egg-info

# Run tests with coverage.
# coverage:
# 	python -m coverage erase
# 	python -m coverage run -m unittest
# 	python -m coverage report

# Install any dependencies for running tests or coverage.
deps:
	pip install -e .

# Run tests.
# test:
# 	python -m unittest discover -s ./tests -p test*.py -v
