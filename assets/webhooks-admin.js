(function () {
  const state = {
    meta: null,
    webhooks: [],
    templateDrafts: {},
    payloadTemplateDrafts: {},
  };
  let $ = null;
  let ezToast = null;
  let ezQuery = null;
  let modal = null;

  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    if (window.CTFd && window.CTFd.lib && window.CTFd.lib.$) {
      $ = window.CTFd.lib.$;
    }
    if (window.CTFd && window.CTFd.ui && window.CTFd.ui.ezq) {
      ezToast = window.CTFd.ui.ezq.ezToast;
      ezQuery = window.CTFd.ui.ezq.ezQuery;
    }
    if ($) {
      modal = $("#webhook-modal");
      modal.on("hidden.bs.modal", function () {
        resetForm();
      });
    }

    bindEvents();

    try {
      const [meta, webhooks] = await Promise.all([
        apiRequest("/meta"),
        apiRequest("/webhooks"),
      ]);
      state.meta = meta;
      state.webhooks = webhooks;
      renderFormOptions();
      renderTable();
      resetForm();
      syncTableOverflowState();
    } catch (error) {
        notify(
          "Webhook page failed to load",
          error.message || "Failed to load webhook configuration",
          "error",
        );
    }
  }

  function bindEvents() {
    document
      .getElementById("webhook-form")
      .addEventListener("submit", onSubmitForm);
    document
      .getElementById("webhook-new-button")
      .addEventListener("click", openCreateModal);
    document
      .getElementById("webhook-table-body")
      .addEventListener("click", onTableAction);
    document
      .getElementById("webhook-events")
      .addEventListener("change", onTemplateSelectionChange);
    document
      .getElementById("webhook-template-editors")
      .addEventListener("input", onTemplateInput);

    const tableScroller = document.getElementById("webhook-table-scroller");
    tableScroller.addEventListener("scroll", syncTableOverflowState);
    window.addEventListener("resize", syncTableOverflowState);
  }

  async function onSubmitForm(event) {
    event.preventDefault();

    const webhookId = document.getElementById("webhook-id").value;
    const payload = collectFormPayload();
    const target = webhookId ? `/webhooks/${webhookId}` : "/webhooks";
    const method = webhookId ? "PATCH" : "POST";

    try {
      const webhook = await apiRequest(target, { method, body: payload });
      upsertWebhook(webhook);
      renderTable();
      resetForm();
      closeModal();
      syncTableOverflowState();
      notify(
        webhookId ? "Webhook updated" : "Webhook created",
        webhookId
          ? "The webhook configuration has been updated."
          : "The webhook has been created and is ready to use.",
      );
    } catch (error) {
      notify("Webhook save failed", error.message || "Failed to save webhook", "error");
    }
  }

  async function onTableAction(event) {
    const actionButton = event.target.closest("[data-action]");
    if (!actionButton) {
      return;
    }

    const webhookId = Number(actionButton.dataset.webhookId);
    const action = actionButton.dataset.action;
    const webhook = state.webhooks.find((item) => item.id === webhookId);

    if (!webhook) {
        notify("Webhook missing", "Webhook no longer exists", "error");
      return;
    }

    if (action === "edit") {
      openEditModal(webhook);
      return;
    }

    if (action === "delete") {
      confirmDelete(webhook);
      return;
    }

    if (action === "pause" || action === "resume") {
      try {
        const updatedWebhook = await apiRequest(`/webhooks/${webhookId}/${action}`, {
          method: "POST",
        });
        upsertWebhook(updatedWebhook);
        renderTable();
        syncTableOverflowState();
        if (String(document.getElementById("webhook-id").value) === String(webhookId)) {
          populateForm(updatedWebhook);
        }
        notify(
          action === "pause" ? "Webhook paused" : "Webhook resumed",
            action === "pause"
              ? "Deliveries are paused for this webhook."
              : "Deliveries are active for this webhook again.",
        );
      } catch (error) {
        notify(
          "Webhook update failed",
          error.message || "Failed to update webhook state",
          "error",
        );
      }
    }
  }

  function collectFormPayload() {
    const eventTemplates = {};
    const eventPayloadTemplates = {};
    document.querySelectorAll("textarea[data-event-template]").forEach((textarea) => {
      eventTemplates[textarea.dataset.eventTemplate] = textarea.value;
    });
    document.querySelectorAll("textarea[data-event-payload-template]").forEach((textarea) => {
      eventPayloadTemplates[textarea.dataset.eventPayloadTemplate] = textarea.value;
    });

    return {
      name: document.getElementById("webhook-name").value.trim(),
      provider: document.getElementById("webhook-provider").value,
      target_url: document.getElementById("webhook-target-url").value.trim(),
      is_private: document.getElementById("webhook-is-private").checked,
      event_types: Array.from(
        document.querySelectorAll('input[name="event_types"]:checked'),
      ).map((input) => input.value),
      event_templates: eventTemplates,
      event_payload_templates: eventPayloadTemplates,
    };
  }

  function renderFormOptions() {
    const providerSelect = document.getElementById("webhook-provider");
    providerSelect.innerHTML = state.meta.providers
      .map(
        (provider) =>
          `<option value="${escapeHtml(provider.value)}">${escapeHtml(
            provider.label,
          )}</option>`,
      )
      .join("");

    const eventsContainer = document.getElementById("webhook-events");
    eventsContainer.innerHTML = state.meta.events
      .map(
        (eventOption) => `
          <div class="webhook-event-option">
            <label>
              <input type="checkbox" name="event_types" value="${escapeHtml(
                eventOption.value,
              )}"> ${escapeHtml(eventOption.label)}
            </label>
            <small>${escapeHtml(eventOption.description || "")}</small>
          </div>
        `,
      )
      .join("");

    const hints = document.getElementById("webhook-template-hints");
    hints.innerHTML = state.meta.template_variable_hints
      .map(
        (hint) => `<span class="webhook-template-hint">${escapeHtml(hint)}</span>`,
      )
      .join("");

    syncTemplateEditors();
  }

  function renderTable() {
    const tableBody = document.getElementById("webhook-table-body");

    if (!state.webhooks.length) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">No webhooks registered yet.</td>
        </tr>
      `;
      syncTableOverflowState();
      return;
    }

    tableBody.innerHTML = state.webhooks
      .map((webhook) => {
        const hookLabels = webhook.event_types
          .map((eventType) => eventLabel(eventType))
          .join(", ");
        const statusClass = webhook.is_paused
          ? "webhook-status webhook-status-paused"
          : "webhook-status webhook-status-active";
        const statusLabel = webhook.is_paused ? "Paused" : "Active";
        const visibilityClass = webhook.is_private
          ? "webhook-status webhook-status-private"
          : "webhook-status webhook-status-public";
        const visibilityLabel = webhook.is_private ? "Private" : "Public";
        const lastDelivery = webhook.last_success_at
          ? `Last success ${formatTimestamp(webhook.last_success_at)}`
          : webhook.last_attempt_at
            ? `Last attempt ${formatTimestamp(webhook.last_attempt_at)}`
            : "Never";

        return `
          <tr>
            <td>
              <strong>${escapeHtml(webhook.name || "Unnamed webhook")}</strong>
              <span class="small text-muted webhook-muted-url">${escapeHtml(
                webhook.target_url,
              )}</span>
            </td>
            <td>${escapeHtml(providerLabel(webhook.provider))}</td>
            <td>
              <span class="${visibilityClass}">${visibilityLabel}</span>
              <div class="mt-1">
              <span class="${statusClass}">${statusLabel}</span>
              </div>
              ${
                webhook.last_error
                  ? `<div class="small text-danger webhook-last-error" title="${escapeHtml(
                      webhook.last_error,
                    )}">${escapeHtml(webhook.last_error)}</div>`
                  : ""
              }
            </td>
            <td class="small">${escapeHtml(hookLabels)}</td>
            <td class="small">${escapeHtml(lastDelivery)}</td>
            <td>
              <div class="webhook-inline-actions">
                <button type="button" class="btn btn-sm btn-outline-primary" data-action="edit" data-webhook-id="${webhook.id}">Edit</button>
                <button type="button" class="btn btn-sm btn-outline-${
                  webhook.is_paused ? "success" : "warning"
                }" data-action="${webhook.is_paused ? "resume" : "pause"}" data-webhook-id="${webhook.id}">${
                  webhook.is_paused ? "Resume" : "Pause"
                }</button>
                <button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-webhook-id="${webhook.id}">Delete</button>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");

    syncTableOverflowState();
  }

  function populateForm(webhook) {
    state.templateDrafts = buildDefaultTemplateDrafts();
    state.payloadTemplateDrafts = buildDefaultPayloadTemplateDrafts();
    Object.entries(webhook.event_templates || {}).forEach(([eventType, template]) => {
      state.templateDrafts[eventType] = template;
    });
    Object.entries(webhook.event_payload_templates || {}).forEach(
      ([eventType, payloadTemplate]) => {
        state.payloadTemplateDrafts[eventType] = payloadTemplate;
      },
    );

    document.getElementById("webhook-id").value = webhook.id;
    document.getElementById("webhook-name").value = webhook.name || "";
    document.getElementById("webhook-provider").value = webhook.provider;
    document.getElementById("webhook-target-url").value = webhook.target_url;
    document.getElementById("webhook-is-private").checked = !!webhook.is_private;

    document.querySelectorAll('input[name="event_types"]').forEach((input) => {
      input.checked = webhook.event_types.includes(input.value);
    });
    syncTemplateEditors();

    document.getElementById("webhook-modal-title").textContent = "Edit webhook";
    document.getElementById("webhook-submit-button").textContent = "Save changes";
  }

  function resetForm() {
    document.getElementById("webhook-form").reset();
    document.getElementById("webhook-id").value = "";
    state.templateDrafts = buildDefaultTemplateDrafts();
    state.payloadTemplateDrafts = buildDefaultPayloadTemplateDrafts();
    document.getElementById("webhook-modal-title").textContent = "Create webhook";
    document.getElementById("webhook-submit-button").textContent = "Create webhook";
    if (state.meta && state.meta.providers.length) {
      document.getElementById("webhook-provider").value = state.meta.providers[0].value;
    }
    document.getElementById("webhook-is-private").checked = false;
    document.querySelectorAll('input[name="event_types"]').forEach((input) => {
      input.checked = false;
    });
    syncTemplateEditors();
  }

  function resetFormIfEditingDeleted(webhookId) {
    if (String(document.getElementById("webhook-id").value) === String(webhookId)) {
      resetForm();
    }
  }

  function openCreateModal() {
    resetForm();
    openModal();
  }

  function openEditModal(webhook) {
    populateForm(webhook);
    openModal();
  }

  function openModal() {
    if (modal) {
      modal.modal("show");
      return;
    }
    document.getElementById("webhook-modal").classList.add("show");
  }

  function closeModal() {
    if (modal) {
      modal.modal("hide");
      return;
    }
    document.getElementById("webhook-modal").classList.remove("show");
  }

  function confirmDelete(webhook) {
    const targetName = webhook.name || webhook.target_url;
    if (ezQuery) {
      ezQuery({
        title: "Delete Webhook",
        body: `Are you sure you want to delete ${escapeHtml(targetName)}?`,
        success: function () {
          performDelete(webhook.id);
        },
      });
      return;
    }

    if (window.confirm(`Delete webhook ${targetName}?`)) {
      performDelete(webhook.id);
    }
  }

  async function performDelete(webhookId) {
    try {
      await apiRequest(`/webhooks/${webhookId}`, { method: "DELETE" });
      state.webhooks = state.webhooks.filter((item) => item.id !== webhookId);
      renderTable();
      syncTableOverflowState();
      resetFormIfEditingDeleted(webhookId);
        notify("Webhook deleted", "The webhook has been removed.");
    } catch (error) {
      notify("Webhook delete failed", error.message || "Failed to delete webhook", "error");
    }
  }

  function upsertWebhook(webhook) {
    const existingIndex = state.webhooks.findIndex((item) => item.id === webhook.id);
    if (existingIndex >= 0) {
      state.webhooks.splice(existingIndex, 1, webhook);
      return;
    }
    state.webhooks.unshift(webhook);
  }

  async function apiRequest(path, options = {}) {
    const fetchOptions = {
      method: options.method || "GET",
      headers: {},
    };

    if (options.body !== undefined) {
      fetchOptions.headers["Content-Type"] = "application/json";
      fetchOptions.body = JSON.stringify(options.body);
    }

    const response = await CTFd.fetch(
      `/plugins/ctfd-plugin-webhooks/api/v1${path}`,
      fetchOptions,
    );

    let payload = {};
    try {
      payload = await response.json();
    } catch (_error) {
      payload = {};
    }

    if (!response.ok || payload.success === false) {
      throw new Error(extractErrorMessage(payload, response.status));
    }

    return payload.data;
  }

  function extractErrorMessage(payload, statusCode) {
    if (payload && payload.errors) {
      return Object.entries(payload.errors)
        .map(([field, messages]) => `${field}: ${messages.join(", ")}`)
        .join(" | ");
    }
    if (payload && payload.message) {
      return payload.message;
    }
    return `Request failed (${statusCode})`;
  }

  function providerLabel(value) {
    const provider = state.meta.providers.find((item) => item.value === value);
    return provider ? provider.label : value;
  }

  function eventLabel(value) {
    const eventOption = state.meta.events.find((item) => item.value === value);
    return eventOption ? eventOption.label : value;
  }

  function formatTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  }

  function notify(title, body, tone = "success") {
    if (ezToast) {
      ezToast({
        title,
        body,
        delay: tone === "error" ? 12000 : 5000,
      });
      return;
    }

    window.alert(`${title}: ${body}`);
  }

  function syncTableOverflowState() {
    const shell = document.getElementById("webhook-table-shell");
    const scroller = document.getElementById("webhook-table-scroller");
    const hint = document.getElementById("webhook-scroll-hint");

    if (!shell || !scroller || !hint) {
      return;
    }

    const overflowAmount = scroller.scrollWidth - scroller.clientWidth;
    const hasOverflow = overflowAmount > 8;
    const leftVisible = scroller.scrollLeft > 8;
    const rightVisible = scroller.scrollLeft < overflowAmount - 8;

    shell.classList.toggle("is-scrollable-left", hasOverflow && leftVisible);
    shell.classList.toggle("is-scrollable-right", hasOverflow && rightVisible);
    hint.classList.toggle("d-none", !hasOverflow);
  }

  function onTemplateSelectionChange(_event) {
    persistVisibleTemplateDrafts();
    syncTemplateEditors();
  }

  function onTemplateInput(event) {
    const textarea = event.target.closest("textarea[data-event-template]");
    if (textarea) {
      state.templateDrafts[textarea.dataset.eventTemplate] = textarea.value;
      return;
    }

    const payloadTextarea = event.target.closest(
      "textarea[data-event-payload-template]",
    );
    if (payloadTextarea) {
      state.payloadTemplateDrafts[payloadTextarea.dataset.eventPayloadTemplate] =
        payloadTextarea.value;
    }
  }

  function syncTemplateEditors() {
    const container = document.getElementById("webhook-template-editors");
    if (!container || !state.meta) {
      return;
    }

    persistVisibleTemplateDrafts();

    const selectedEventTypes = Array.from(
      document.querySelectorAll('input[name="event_types"]:checked'),
    ).map((input) => input.value);

    if (!selectedEventTypes.length) {
      container.innerHTML = '<div class="webhook-template-empty">Select one or more hook types to edit their message and payload templates.</div>';
      return;
    }

    container.innerHTML = selectedEventTypes
      .map((eventType) => {
        const eventOption = state.meta.events.find((item) => item.value === eventType);
        const template = state.templateDrafts[eventType] || eventOption.default_template || "";
        const payloadTemplate = state.payloadTemplateDrafts[eventType] || "";
        return `
          <div class="webhook-template-card">
            <div class="webhook-template-card-header">
              <strong>${escapeHtml(eventOption.label)}</strong>
              <small>${escapeHtml(eventOption.description || "")}</small>
            </div>
            <div class="webhook-template-card-body">
              <label class="webhook-template-label" for="webhook-template-${escapeHtml(eventType)}">Message text</label>
              <textarea id="webhook-template-${escapeHtml(eventType)}" class="form-control" data-event-template="${escapeHtml(eventType)}">${escapeHtml(template)}</textarea>
              <small class="form-text text-muted webhook-template-help">Used by the built-in Discord formatter and included as <code>message</code> in the canonical JSON payload.</small>
              <label class="webhook-template-label mt-3" for="webhook-payload-template-${escapeHtml(eventType)}">JSON payload override</label>
              <textarea id="webhook-payload-template-${escapeHtml(eventType)}" class="form-control webhook-template-json" data-event-payload-template="${escapeHtml(eventType)}" placeholder='{"embeds": [{"title": {{ challenge.name|tojson }}, "description": {{ message|tojson }}}]}'>${escapeHtml(payloadTemplate)}</textarea>
              <small class="form-text text-muted webhook-template-help">Optional. If set, this rendered JSON replaces the default request body for this event. Use <code>|tojson</code> for values inside JSON, for example <code>"category": {{ challenge.category|tojson }}</code>.</small>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function persistVisibleTemplateDrafts() {
    document.querySelectorAll("textarea[data-event-template]").forEach((textarea) => {
      state.templateDrafts[textarea.dataset.eventTemplate] = textarea.value;
    });
    document.querySelectorAll("textarea[data-event-payload-template]").forEach((textarea) => {
      state.payloadTemplateDrafts[textarea.dataset.eventPayloadTemplate] = textarea.value;
    });
  }

  function buildDefaultTemplateDrafts() {
    const drafts = {};
    if (!state.meta) {
      return drafts;
    }
    state.meta.events.forEach((eventOption) => {
      drafts[eventOption.value] = eventOption.default_template || "";
    });
    return drafts;
  }

  function buildDefaultPayloadTemplateDrafts() {
    const drafts = {};
    if (!state.meta) {
      return drafts;
    }
    state.meta.events.forEach((eventOption) => {
      drafts[eventOption.value] = "";
    });
    return drafts;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();