AssessFrontend.FilteredFetchTable = function(params) {
	this.container = params.container;
	this.table = this.container.querySelector('table');
	this.body = this.table.querySelector('tbody');
	this.searchForm = this.container.querySelector('.fsd-table-search-form');
	this.filters = new FormData(this.searchForm);
	this.sortButtons = this.container.querySelectorAll('.fsd-table-sort-button');
	this.filterLinks = this.container.querySelectorAll('.fsd-table-filter-link');
	this.filterForms = this.container.querySelectorAll('.fsd-table-filter-form');
	this.headings = this.table.querySelectorAll('thead th');
	this.cols = this.headings.length;
	this.endpoint = this.container.dataset.endpoint;
	this.loading = false;
	this.results = [];

	if (this.container.dataset.initialised) {
		return
	}

	this.container.dataset.initialised = "ok";

	this.setupOptions(params);
	this.setupFilters();
};

AssessFrontend.FilteredFetchTable.prototype.setupOptions = function(params) {
	params = params || {};
};



AssessFrontend.FilteredFetchTable.prototype.setupFilters = function(params) {
	this.activateSearchForm();
	this.activateFilterForms();
	this.activateLinks();
};

AssessFrontend.FilteredFetchTable.prototype.clearRows = function() {
	[...this.body.children].forEach(function(row){row.remove();});
}

AssessFrontend.FilteredFetchTable.prototype.updateResults = function() {
	this.clearRows();
	if(this.results.length > 0) {
		this.addRows();
	} else {
		this.setNoResults();
	}
	this.updateFilterStates();
	this.updateSortButtonStates();
};

AssessFrontend.FilteredFetchTable.prototype.setNoResults = function() {
	this.loading = false;
	this.results = [];
	let tr = this.body.insertRow(0)
	tr.id = "filtered-table-rows-response"
	let td = tr.insertCell()
	td.colSpan = this.cols;
	td.innerText = "No results found";
};

AssessFrontend.FilteredFetchTable.prototype.fetchData = async function() {
	this.setLoading();
	let params = new URLSearchParams(this.filters).toString();
	let endpoint = this.endpoint + params
	let res = await fetch(endpoint);
	this.results = await res.json();
	this.updateResults();
	this.setDoneLoading();
};

AssessFrontend.FilteredFetchTable.prototype.clickLink = function(e) {
	e.preventDefault();
	let filterKey = e.target.dataset.filterKey;
	let filterValue = e.target.dataset.filterValue;
	this.filters.set(filterKey, filterValue);
	this.fetchData();
};

AssessFrontend.FilteredFetchTable.prototype.filterFormOnSubmit = function(e) {
	e.preventDefault();
	let sortKey = e.target.dataset.sortKey;
	let orderRev = "";
	if (this.filters.get("order_by") && this.filters.get("order_by") == sortKey) {
		if (this.filters.get("order_rev") != "1") {
			orderRev = "1";
		} else {
			orderRev = "";
		}
	}
	this.filters.set("order_by", sortKey);
	this.filters.set("order_rev", orderRev);
	this.fetchData();
};

AssessFrontend.FilteredFetchTable.prototype.searchFormOnSubmit = function(e) {
	e.preventDefault();
	let searchKey = this.searchForm.dataset.searchKey;
	let searchInput = this.searchForm.querySelector(`input[name=${searchKey}]`)
	this.filters.set(searchKey, searchInput.value);
	this.fetchData();
};

AssessFrontend.FilteredFetchTable.prototype.activateFilterForms = function() {
	let fetchTable = this;
	this.filterForms.forEach(function(form) {
		form.addEventListener('submit', fetchTable.filterFormOnSubmit.bind(fetchTable));
	});
};

AssessFrontend.FilteredFetchTable.prototype.activateSearchForm = function() {
	let fetchTable = this;
	this.searchForm.addEventListener('submit', fetchTable.searchFormOnSubmit.bind(fetchTable));
	this.searchForm.addEventListener('input', fetchTable.searchFormOnSubmit.bind(fetchTable));
};

AssessFrontend.FilteredFetchTable.prototype.activateLinks = function() {
	let fetchTable = this;
	this.filterLinks.forEach(function(link) {
		link.addEventListener('click', fetchTable.clickLink.bind(fetchTable));
	});
};

AssessFrontend.FilteredFetchTable.prototype.updateSortButtonStates = function() {
	let filters = this.filters;
	this.sortButtons.forEach(function(sortButton) {
		let sort = "none";
		if (filters.get("order_by") && filters.get("order_by") == sortButton.dataset.sortKey) {
			if (filters.get("order_rev") && filters.get("order_rev") == "1") {
				sort = "ascending";
			} else {
				sort = "descending"
			}
		}
		sortButton.setAttribute('aria-sort', sort);
	});
};

AssessFrontend.FilteredFetchTable.prototype.updateFilterStates = function() {
	let filters = this.filters;
	this.filterLinks.forEach(function(link) {
		let selected = false;
		if (filters.get(link.dataset.filterKey) && filters.get(link.dataset.filterKey) == link.dataset.filterValue) {
			selected = true;
		} else if (!filters.get(link.dataset.filterKey) && link.dataset.filterValue == "") {
			selected = true;
		}
		link.setAttribute('aria-selected', selected);
	});
};

AssessFrontend.FilteredFetchTable.prototype.formatContent = function(col, data) {
	let responseKey = col.dataset.responseKey;
	let responseType = col.dataset.responseType;
	if (responseType == "date") {
		let date = new Date(data[responseKey]);
		let date_els = date.toDateString().split(" ")
		return [date_els[2], date_els[1], date_els[3]].join(" ");
	} else if (responseType == "status") {
		if (data[responseKey] == 'COMPLETED') {
			return `<strong class="govuk-tag">COMPLETED</strong>`
		} else if (data[responseKey] == 'ASSESSING') {
			return `<strong class="govuk-tag govuk-tag--blue">ASSESSING</strong>`
		} else if (data[responseKey] == 'NOT_STARTED') {
			return `<strong class="govuk-tag govuk-tag--grey">NOT STARTED</strong>`
		} else {
			return `<strong class="govuk-tag govuk-tag--grey">${data[responseKey]}</strong>`
		}
	} else if (responseType == "id") {
		return `<a href="/assess/application/${data[responseKey]}" class="govuk-link fsd-application-link">${data[responseKey]}</a>`
	} else {
		return data[responseKey];
	}
};

AssessFrontend.FilteredFetchTable.prototype.addRow = function(data) {
	let tr = this.body.insertRow();
	tr.className = "govuk-table__row";
	for(let i = 0; i < this.headings.length; i++) {
		let col = this.headings[i];
		let td = tr.insertCell();
		td.className = "govuk-table__cell";
		td.innerHTML = this.formatContent(col, data);
	}
};

AssessFrontend.FilteredFetchTable.prototype.addRows = function() {
	for(let i = 0; i < this.results.length; i++) {
		this.addRow(this.results[i]);
	}
};

AssessFrontend.FilteredFetchTable.prototype.setLoading = function() {
	this.loading = true;
	this.results = [];
};

AssessFrontend.FilteredFetchTable.prototype.setDoneLoading = function() {
	this.loading = false;
};
