# Cấu Trúc Schema Mẫu Cho Interaction Flow (Examples)

## Mẫu Schema Form Thu Thập Thông Tin Khách Hàng (2 Bước)

```json
{
  "title": "Khảo sát nhu cầu tư vấn sản phẩm",
  "steps": [
    {
      "stepId": "step_contact",
      "title": "Thông tin liên hệ",
      "fields": [
        {
          "fieldId": "customer_name",
          "type": "text",
          "label": "Họ và tên",
          "required": true,
          "placeholder": "Nguyễn Văn A"
        },
        {
          "fieldId": "phone_number",
          "type": "text",
          "label": "Số điện thoại",
          "required": true,
          "validation": {
            "regex": "^0[0-9]{9}$",
            "message": "Số điện thoại phải có 10 chữ số bắt đầu bằng số 0"
          }
        }
      ]
    },
    {
      "stepId": "step_preference",
      "title": "Nhu cầu mua sắm",
      "fields": [
        {
          "fieldId": "device_category",
          "type": "select",
          "label": "Loại thiết bị quan tâm",
          "required": true,
          "options": [
            { "label": "Laptop Gaming", "value": "laptop_gaming" },
            { "label": "Laptop Văn Phòng", "value": "laptop_office" },
            { "label": "Linh kiện PC", "value": "pc_parts" }
          ]
        },
        {
          "fieldId": "budget_range",
          "type": "radio",
          "label": "Mức ngân sách dự kiến",
          "required": false,
          "options": [
            { "label": "Dưới 15 triệu", "value": "under_15m" },
            { "label": "Từ 15 - 30 triệu", "value": "15m_to_30m" },
            { "label": "Trên 30 triệu", "value": "above_30m" }
          ]
        }
      ]
    }
  ],
  "submitAction": {
    "operationId": "submit_lead_inquiry",
    "mapping": {
      "name": "{{fields.customer_name}}",
      "phone": "{{fields.phone_number}}",
      "category": "{{fields.device_category}}",
      "budget": "{{fields.budget_range}}"
    }
  }
}
```
