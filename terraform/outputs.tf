output "resource_group_name" {
  value = azurerm_resource_group.energy.name
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "postgresql_server_name" {
  value = azurerm_postgresql_flexible_server.energy.name
}