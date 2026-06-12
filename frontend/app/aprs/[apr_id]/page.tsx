import { ControlRoomView } from "@/features/control-room/components/ControlRoomView";

export default async function AprDetailPage({
  params,
}: {
  params: Promise<{ apr_id: string }>;
}) {
  const { apr_id } = await params;
  return <ControlRoomView aprId={apr_id} />;
}
