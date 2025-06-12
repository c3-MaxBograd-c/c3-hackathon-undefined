SEMANTIC_VERSION_MANAGER := scripts/semantic-version-manager/semantic-version-manager.py

component ?= ""
path ?= ""
package ?= ""
version ?= ""

version-bump:
	@python $(SEMANTIC_VERSION_MANAGER) version-bump $(component) $(path)

version-dependency:
	@python $(SEMANTIC_VERSION_MANAGER) version-dependency $(package) $(version) $(path)

version-validate:
	@python $(SEMANTIC_VERSION_MANAGER) version-validate $(path)

version-update:
	@python $(SEMANTIC_VERSION_MANAGER) version-update $(version) $(path)
