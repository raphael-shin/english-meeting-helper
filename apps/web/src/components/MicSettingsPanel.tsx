import { useEffect, useState } from "react";

import { ProviderMode } from "../types/provider";

interface AudioDeviceOption {
  deviceId: string;
  label: string;
}

interface MicSettingsPanelProps {
  providerMode: ProviderMode;
  onProviderModeChange: (mode: ProviderMode) => void;
}

export function MicSettingsPanel({
  providerMode,
  onProviderModeChange,
}: MicSettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [devices, setDevices] = useState<AudioDeviceOption[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const loadDevices = async () => {
      try {
        let items = await navigator.mediaDevices.enumerateDevices();
        let microphones = items.filter((item) => item.kind === "audioinput");

        // If no labels, we likely don't have permission yet.
        // Try to ask for permission briefly.
        const hasLabels = microphones.some((m) => m.label.length > 0);
        if (microphones.length === 0 || !hasLabels) {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({
              audio: true,
            });
            // Stop immediately, we just wanted the permission
            stream.getTracks().forEach((track) => track.stop());

            // Re-enumerate after permission
            items = await navigator.mediaDevices.enumerateDevices();
            microphones = items.filter((item) => item.kind === "audioinput");
          } catch (err) {
            console.warn("Microphone permission denied", err);
            setStatus("Permission denied");
            return;
          }
        }

        const options = microphones.map((item) => ({
          deviceId: item.deviceId,
          label: item.label || `Microphone ${item.deviceId.slice(0, 4)}...`,
        }));

        setDevices(options);

        // Only set default if not already selected
        if (!selectedDeviceId && options.length > 0) {
          setSelectedDeviceId(options[0].deviceId);
        }
      } catch (error) {
        console.error(error);
        setStatus("Unable to list microphones");
      }
    };

    loadDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const handleTest = async () => {
    if (!selectedDeviceId) {
      setStatus("Select a microphone first");
      return;
    }
    try {
      setIsTesting(true);
      setStatus("Testing microphone...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: { exact: selectedDeviceId } },
      });
      window.setTimeout(() => {
        stream.getTracks().forEach((track) => track.stop());
        setIsTesting(false);
        setStatus("Test complete");
      }, 2000);
    } catch (error) {
      setIsTesting(false);
      setStatus("Microphone test failed");
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen((open) => !open)}
        className="rounded-full border border-white/70 bg-white/80 px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-white"
        aria-label="Microphone settings"
      >
        Settings
      </button>
      {isOpen && (
        <div className="absolute right-0 top-12 z-10 w-64 rounded-2xl border border-white/70 bg-white/95 p-3 shadow-xl backdrop-blur">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-600">
              Provider
            </label>
            <select
              value={providerMode}
              onChange={(event) =>
                onProviderModeChange(event.target.value as ProviderMode)
              }
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
            >
              <option value="AWS">AWS</option>
              <option value="OPENAI">OpenAI</option>
            </select>
            <label className="text-xs font-semibold text-slate-600">
              Microphone
            </label>
            <select
              value={selectedDeviceId}
              onChange={(event) => setSelectedDeviceId(event.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
            >
              {devices.length === 0 ? (
                <option value="">No devices</option>
              ) : (
                devices.map((device) => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label}
                  </option>
                ))
              )}
            </select>
            <button
              onClick={handleTest}
              disabled={isTesting}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed"
            >
              {isTesting ? "Testing..." : "Test microphone"}
            </button>
            {status && <p className="text-xs text-slate-500">{status}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
