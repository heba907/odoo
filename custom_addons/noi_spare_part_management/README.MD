# Spare Part Management

## Overview
Spare Part Management is an Odoo 15 module that facilitates the management of spare parts, tracking stock levels, and linking child components to parent products.  
It enhances inventory control by introducing structured spare part handling with dedicated stock locations and flows.

---

## ✨ Features
- Manage spare parts for main products.
- Add a **Spare Part Tab** in the product form (for components).
- Track stock movements and quantities.
- Link child components to parent products.
- Automate stock movement between **Temporary Location (usage=transit)** and **Spare Production (usage=production)**.
- Confirm and validate stock transactions.
- Support returns and cancellations of stock operations.

---

## ⚙️ Installation
1. Copy the module folder into the `addons` directory of your Odoo installation.
2. Restart the Odoo server.
3. Activate Developer Mode in Odoo.
4. Navigate to *Apps* and search for **Spare Part Management**.
5. Click **Install**.

---

## 📦 Dependencies
This module depends on the following Odoo apps:
- `stock`
- `analytic_account`
- `sale_api_extend`

---

## 📂 Data Files
- `security/ir.model.access.csv`: Defines access rights and security rules.
- `data/tempory_location.xml`: Creates locations for:
  - **Temporary Location** (`usage=transit`)
  - **Spare Production** (`usage=production`)
- `views/spare_part_stock_view.xml`: Provides forms, tree views, and menus for spare part management.
- `wizards/spare_part_confirm_wizard.xml`: Defines confirmation wizards for stock actions.
- `static/description/index.html`: Spare part flow documentation with YouTube reference.

---

## 🗂 Models
### `models/product.py`
Extends product configuration to support **Spare Part Tab**.

### `models/spare_part_stock.py`
Main model for spare part management:
- Stock tracking
- Stock moves between locations
- Reverse transactions

### `models/stock_move.py`
Defines spare part stock move logic and validation.

---

## 🔐 Security
Access control rules are provided in:  
📄 `security/ir.model.access.csv`  
They restrict permissions by user roles to ensure secure handling of spare part stock.

---

## 🔄 Workflow
1. **Stock Management**
   - Register spare parts under **Products** or **Inventory > Spare Part**.
   - Track spare part stock levels in real time.
   - Manage stock in `temporary_location` and `production_location`.

2. **Stock Movement Confirmation**
   - Confirm stock moves via **Spare Part Confirm Wizard**.
   - Validate transactions to prevent discrepancies.

3. **Stock Processing**
   - Automatic stock moves based on predefined rules.
   - Manual adjustments possible when required.

4. **Return & Cancellation**
   - Return defective or incorrect parts.
   - Cancel transactions to revert stock state.

---

## 📌 Version
- **15.0.1.0.0**  
- Maintainer: **Rowan Ember**

---

## 👤 Author Information
- **Author:** NexOrionis Techsphere  
- **Company:** NexOrionis Techsphere  
- **Maintainer:** Rowan Ember  
- **Website:** [NexOrionis Techsphere](https://nexorionis.odoo.com)  
- **License:** LGPL-3  

---

## 📩 Support
For issues, feature requests, or support:  
📧 [nexorionis.info@gmail.com](mailto:nexorionis.info@gmail.com)  
🌐 [https://nexorionis.site](https://nexorionis.site)  
