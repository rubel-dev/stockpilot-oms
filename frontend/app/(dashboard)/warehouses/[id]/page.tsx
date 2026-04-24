import { WarehouseDetailScreen } from "@/features/warehouses/warehouse-detail-screen";

export default async function WarehouseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <WarehouseDetailScreen id={id} />;
}

