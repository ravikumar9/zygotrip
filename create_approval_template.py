"""
Simple HTML template for admin approval queue
Template: templates/admin/hotels/approval_queue.html
"""

APPROVAL_QUEUE_TEMPLATE = """
{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<div class="approval-queue-container" style="padding: 20px;">
  <h1>{{ title }}</h1>
  
  <!-- Stats Cards -->
  <div class="stats-row" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
    <div class="stat-card" style="background: #fff3cd; padding: 1rem; border-radius: 8px;">
      <div style="font-size: 2rem; font-weight: bold;">{{ stats.pending_count }}</div>
      <div style="color: #856404;">Pending Review</div>
    </div>
    <div class="stat-card" style="background: #d1ecf1; padding: 1rem; border-radius: 8px;">
      <div style="font-size: 2rem; font-weight: bold;">{{ stats.approved_count }}</div>
      <div style="color: #0c5460;">Manually Approved</div>
    </div>
    <div class="stat-card" style="background: #d4edda; padding: 1rem; border-radius: 8px;">
      <div style="font-size: 2rem; font-weight: bold;">{{ stats.auto_approved_count }}</div>
      <div style="color: #155724;">Auto-Approved</div>
    </div>
    <div class="stat-card" style="background: #f8d7da; padding: 1rem; border-radius: 8px;">
      <div style="font-size: 2rem; font-weight: bold;">{{ stats.rejected_count }}</div>
      <div style="color: #721c24;">Rejected</div>
    </div>
  </div>
  
  <!-- Settings Info -->
  <div class="settings-info" style="background: #e7f3ff; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
    <strong>Auto-Approval Settings:</strong>
    {% if settings.auto_approve_enabled %}
      ✅ Enabled - Changes auto-approve after {{ settings.auto_approve_hours }} hours
    {% else %}
      ❌ Disabled - All changes require manual approval
    {% endif %}
    <a href="{% url 'admin:approval_settings' %}" style="margin-left: 1rem;">Edit Settings</a>
  </div>
  
  <!-- Filters -->
  <div class="filters" style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
    <form method="get" style="display: flex; gap: 1rem; align-items: end;">
      <div>
        <label for="status">Status:</label>
        <select name="status" id="status" style="padding: 0.5rem;">
          <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>Pending</option>
          <option value="approved" {% if status_filter == 'approved' %}selected{% endif %}>Approved</option>
          <option value="rejected" {% if status_filter == 'rejected' %}selected{% endif %}>Rejected</option>
          <option value="auto_approved" {% if status_filter == 'auto_approved' %}selected{% endif %}>Auto-Approved</option>
          <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All</option>
        </select>
      </div>
      <div>
        <label for="property">Property/Owner:</label>
        <input type="text" name="property" id="property" value="{{ property_filter }}" placeholder="Search..." style="padding: 0.5rem;">
      </div>
      <button type="submit" style="padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Filter</button>
    </form>
  </div>
  
  <!-- Changes Table -->
  <table style="width: 100%; border-collapse: collapse; background: white;">
    <thead style="background: #f8f9fa;">
      <tr>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Property</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Field Changed</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Old Value</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">New Value</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Requested</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Status</th>
        <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #dee2e6;">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for change in changes %}
      <tr style="border-bottom: 1px solid #dee2e6;">
        <td style="padding: 1rem;">
          <strong>{{ change.property.name }}</strong><br>
          <small style="color: #6c757d;">{{ change.property.owner.email }}</small>
        </td>
        <td style="padding: 1rem;">{{ change.field_label|default:change.field_name }}</td>
        <td style="padding: 1rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">{{ change.old_value|truncatewords:10 }}</td>
        <td style="padding: 1rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis;"><strong>{{ change.new_value|truncatewords:10 }}</strong></td>
        <td style="padding: 1rem;">
          {{ change.requested_at|date:"Y-m-d H:i" }}<br>
          <small style="color: #6c757d;">{{ change.requested_at|timesince }} ago</small>
        </td>
        <td style="padding: 1rem;">
          {% if change.status == 'pending' %}
            <span style="background: #fff3cd; color: #856404; padding: 0.25rem 0.5rem; border-radius: 4px;">⏳ Pending</span>
          {% elif change.status == 'approved' %}
            <span style="background: #d1ecf1; color: #0c5460; padding: 0.25rem 0.5rem; border-radius: 4px;">✓ Approved</span>
          {% elif change.status == 'auto_approved' %}
            <span style="background: #d4edda; color: #155724; padding: 0.25rem 0.5rem; border-radius: 4px;">✓ Auto</span>
          {% else %}
            <span style="background: #f8d7da; color: #721c24; padding: 0.25rem 0.5rem; border-radius: 4px;">✗ Rejected</span>
          {% endif %}
        </td>
        <td style="padding: 1rem;">
          {% if change.status == 'pending' %}
            <a href="{% url 'admin:approve_change' change.id %}" style="color: #28a745; margin-right: 0.5rem;">✓ Approve</a>
            <a href="{% url 'admin:reject_change' change.id %}" style="color: #dc3545;">✗ Reject</a>
          {% else %}
            <span style="color: #6c757d;">{{ change.reviewed_by.email|default:"System" }}</span>
          {% endif %}
        </td>
      </tr>
      {% empty %}
      <tr>
        <td colspan="7" style="padding: 2rem; text-align: center; color: #6c757d;">
          No changes found matching your filters.
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
"""

# Save this content to the file
with open('templates/admin/hotels/approval_queue.html', 'w') as f:
	f.write(APPROVAL_QUEUE_TEMPLATE.strip())
