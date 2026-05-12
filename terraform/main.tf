terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# Resource Group — logical container for all resources
resource "azurerm_resource_group" "energy" {
  name     = "rg-energy-pipeline"
  location = var.location
}

# Storage Account with Data Lake Gen2
resource "azurerm_storage_account" "datalake" {
  name                     = "stenergypipeline${var.env}"
  resource_group_name      = azurerm_resource_group.energy.name
  location                 = azurerm_resource_group.energy.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true  # enables Data Lake Gen2
}

# Container inside the storage account (like a top-level folder)
resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "energy" {
  name                   = "psql-energy-pipeline-${var.env}"
  resource_group_name    = azurerm_resource_group.energy.name
  location               = azurerm_resource_group.energy.location
  version                = "15"
  administrator_login    = var.db_admin_user
  administrator_password = var.db_admin_password
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"  # cheapest tier
}

# Key Vault — for storing secrets
resource "azurerm_key_vault" "energy" {
  name                = "kv-energy-${var.env}-mou"
  location            = azurerm_resource_group.energy.location
  resource_group_name = azurerm_resource_group.energy.name
  tenant_id           = var.tenant_id
  sku_name            = "standard"
}