import { ControlRoomView } from '@/features/control-room/components/ControlRoomView';

/**
 * AprDetailPage is the page component for displaying the details of a specific APR plant (Agua Potable Rural).
 * @param param0 - An object containing the route parameters.
 * @param param0.params - A promise that resolves to an object with the `apr_id` parameter, which identifies the
 *   specific APR to display.
 * @returns A React component that renders the ControlRoomView for the specified APR.
 * @constructor
 */
export default async function AprDetailPage({ params }: {
  params: Promise<{ apr_id: string }>;
}) {
  const {apr_id} = await params;

  return <ControlRoomView aprId={apr_id}/>;
}
