AssessFrontend.removeAttributeValue = function(el, attr, value) {
  let re, m;
  if (el.getAttribute(attr)) {
    if (el.getAttribute(attr) == value) {
      el.removeAttribute(attr);
    } else {
      re = new RegExp('(^|\\s)' + value + '(\\s|$)');
      m = el.getAttribute(attr).match(re);
      if (m && m.length == 3) {
        el.setAttribute(attr, el.getAttribute(attr).replace(re, (m[1] && m[2])?' ':''))
      }
    }
  }
}

AssessFrontend.addAttributeValue = function(el, attr, value) {
  let re;
  if (!el.getAttribute(attr)) {
    el.setAttribute(attr, value);
  }
  else {
    re = new RegExp('(^|\\s)' + value + '(\\s|$)');
    if (!re.test(el.getAttribute(attr))) {
      el.setAttribute(attr, el.getAttribute(attr) + ' ' + value);
    }
  }
};

AssessFrontend.nodeListForEach = function (nodes, callback) {
    if (window.NodeList.prototype.forEach) {
        return nodes.forEach(callback)
    }
    for (let i = 0; i < nodes.length; i++) {
        callback.call(window, nodes[i], i, nodes)
    }
};

const showTagsElement = document.getElementById("show-tags");
if (showTagsElement) {
    showTagsElement.addEventListener("change", (event) => {
        const allTagDetails = Array.from(document.getElementsByClassName("dlhuc-tag-expand"));
        const checkboxState = event.target.checked;
        allTagDetails.forEach(tagDetail => {
            tagDetail.open = checkboxState;
        });
    });
}


const tabs = document.querySelectorAll('[id^="tab"]');
const tabAnchors = document.querySelectorAll('.govuk-tabs__tab');
Array.from(tabAnchors).forEach(tabAnchor => {
    tabAnchor.addEventListener('click', (tabAnchorElement) => {
        const hash = tabAnchorElement.target.hash;
        if (hash) {
            Array.from(tabs).forEach((tab) => {
                tab.classList.add('govuk-tabs__panel--hidden');
            });
            Array.from(tabAnchors).forEach((tabA) => {
               tabA.parentElement.classList.remove('govuk-tabs__list-item--selected')
            });

            const activeTab = document.getElementById(hash.replace('#', ''));
            activeTab.classList.remove('govuk-tabs__panel--hidden');
            tabAnchorElement.target.parentElement.classList.add('govuk-tabs__list-item--selected');
        }
    });
})


const select_all_assessments = document.getElementById('select_all_for_assignment')
if (select_all_assessments) {
  select_all_assessments.addEventListener('change', function(e) {
    var checkboxes = document.querySelectorAll('input[name="selected_assessments"]');
    checkboxes.forEach(function(checkbox) {
      checkbox.checked = e.target.checked;
    });
  });
}

const select_all_users = document.getElementById('select_all_users')
if (select_all_users) {
  select_all_users.addEventListener('change', function(e) {
    var checkboxes = document.querySelectorAll('input[name="selected_users"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = e.target.checked;
    });
  });
}

const assessor_messages_checkbox = document.getElementById('assessor_messages_checkbox')
if (assessor_messages_checkbox) {
  assessor_messages_checkbox.addEventListener('change', function() {
    const messagesDiv = document.getElementById('assessor_messages');
    if (assessor_messages_checkbox.checked) {
      messagesDiv.classList.remove('govuk-!-display-none');
      messagesDiv.classList.add('govuk-!-display-block');
  } else {
      messagesDiv.classList.add('govuk-!-display-none');
      messagesDiv.classList.remove('govuk-!-display-block');
  }
  });
}
