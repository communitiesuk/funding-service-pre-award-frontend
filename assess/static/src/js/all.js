AssessFrontend.initAll = function (options) {
  // Set the options to an empty object by default if no options are passed.
  options = typeof options !== 'undefined' ? options : {};

  // Allow the user to initialise Assess Frontend in only certain sections of the page
  // Defaults to the entire document if nothing is set.
  let scope = typeof options.scope !== 'undefined' ? options.scope : document;

  let collapsibleDetails = scope.querySelectorAll(".govuk-details");
  AssessFrontend.nodeListForEach(collapsibleDetails, function (collapsible) {
    new AssessFrontend.Collapsible({
      collapsible: collapsible
    });
  });

  let filteredFetchTables = scope.querySelectorAll('[data-module="fsd-filtered-fetch-table"]');
  AssessFrontend.nodeListForEach(filteredFetchTables, function (container) {
    new AssessFrontend.FilteredFetchTable({
      container: container
    });
  });
}
