import cv2
import threading
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from queue import Queue

from external_dependencies.MessageBroker import MessageBroker
from src.VisionSystem.VisionSystem import VisionSystem

from typing import Tuple, Any
from copy import deepcopy

from src.VisionSystem.core.settings.CameraSettings import CameraSettings
from src.VisionSystem.core.service.interfaces.i_service import IService
from src.VisionSystem.core.external_communication.system_state_management import (
    ServiceState,
    VisionTopics,
)


class FakeSettingsService(IService):
    """
    In-memory fake settings service for testing.
    Does NOT read/write files.
    """

    @property
    def isCalibrated(self) -> bool:
        return False

    def __init__(self, initial_data: CameraSettings | None = None,
                 fail_on_update: bool = False,
                 fail_on_load: bool = False):
        """
        :param initial_data: initial settings dictionary
        :param fail_on_update: simulate update failure
        :param fail_on_load: simulate load failure
        """
        self._settings = initial_data or {}
        self.fail_on_update = fail_on_update
        self.fail_on_load = fail_on_load

    # -----------------------------------------------------

    def loadSettings(self):
        if self.fail_on_load:
            raise RuntimeError("Simulated load failure")

        return deepcopy(self._settings)

    # -----------------------------------------------------

    def updateSettings(self,
                       vision_system,
                       settings: dict,
                       logging_enabled: bool,
                       logger) -> Tuple[bool, str]:

        if self.fail_on_update:
            return False, "FakeSettingsService: simulated update failure"

        try:
            # Merge into internal storage
            self._settings.update(settings)

            # Apply to VisionSystem like real implementation
            success, message = vision_system.camera_settings.updateSettings(settings)

            if not success:
                return False, message

            return True, "Fake settings updated (in-memory)"

        except Exception as e:
            return False, f"FakeSettingsService error: {str(e)}"


    def loadPerspectiveMatrix(self):
        return None

    def loadCameraCalibrationData(self):
        return None

    def loadCameraToRobotMatrix(self):
        return None

    def loadWorkAreaPoints(self):
        return None
    def saveWorkAreaPoints(self, data: Any) -> Tuple[bool, str]:
        return (True, "saveWorkAreaPoints")

    @property
    def cameraData(self):
        return None

    @property
    def cameraToRobotMatrix(self):
        return None

    @property
    def perspectiveMatrix(self):
        return None

    @property
    def camera_to_robot_matrix_path(self):
        return None

    @property
    def sprayAreaPoints(self):
        return None

    def get_camera_matrix(self):
        return None

    def get_distortion_coefficients(self):
        return None


    # -----------------------------------------------------

    # Optional helper for tests
    def get_internal_settings(self) -> dict:
        return deepcopy(self._settings)


class TopicBrokerGUI:
    """Simple GUI for publishing and subscribing to topics via MessageBroker"""

    def __init__(self, root: tk.Tk, broker: MessageBroker):
        self.root = root
        self.broker = broker
        self.root.title("Vision System - Topic Publisher/Subscriber")
        self.root.geometry("900x700")

        self.subscriptions = {}
        self.message_queue = Queue()  # Thread-safe queue for log messages
        self.state_heartbeat_enabled = True  # Enable periodic state polling

        # Topics
        self.topics = [
            VisionTopics.SERVICE_STATE,
            VisionTopics.LATEST_IMAGE,
            VisionTopics.FPS,
            VisionTopics.CALIBRATION_IMAGE_CAPTURED,
            VisionTopics.BRIGHTNESS_REGION,
            VisionTopics.THRESHOLD_REGION,
            VisionTopics.CALIBRATION_FEEDBACK,
            VisionTopics.THRESHOLD_IMAGE,
            VisionTopics.AUTO_BRIGHTNESS,
            VisionTopics.AUTO_BRIGHTNESS_START,
            VisionTopics.AUTO_BRIGHTNESS_STOP,
            VisionTopics.TRANSFORM_TO_CAMERA_POINT,
        ]

        self.sample_payloads = {
            VisionTopics.SERVICE_STATE: {"id": "test-vision", "state": ServiceState.STARTED.value},
            VisionTopics.LATEST_IMAGE: {"timestamp": "2026-02-24T10:00:00"},
            VisionTopics.FPS: {"fps": 30.5},
            VisionTopics.CALIBRATION_IMAGE_CAPTURED: {"image_id": 1},
            VisionTopics.BRIGHTNESS_REGION: {"region": [0, 0, 100, 100]},
            VisionTopics.THRESHOLD_REGION: {"threshold": 127},
            VisionTopics.CALIBRATION_FEEDBACK: {"status": "success"},
            VisionTopics.THRESHOLD_IMAGE: {"image_id": 2},
            VisionTopics.AUTO_BRIGHTNESS: {"enabled": True, "value": 128},
            VisionTopics.AUTO_BRIGHTNESS_START: {"started": True},
            VisionTopics.AUTO_BRIGHTNESS_STOP: {"stopped": True},
            VisionTopics.TRANSFORM_TO_CAMERA_POINT: {"x": 10.5, "y": 20.3, "z": 5.1},
        }

        self._create_widgets()
        self._start_queue_polling()
        self._start_state_heartbeat()  # Start periodic state polling
        # Auto-subscribe to all topics to capture vision system messages
        self.root.after(500, self._auto_subscribe_all)

    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # ===== PUBLISH SECTION =====
        publish_frame = ttk.LabelFrame(main_frame, text="PUBLISH TO TOPIC", padding="10")
        publish_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        publish_frame.columnconfigure(1, weight=1)

        # Topic selection
        ttk.Label(publish_frame, text="Topic:").grid(row=0, column=0, sticky="w", padx=5)
        self.topic_var = tk.StringVar(value=self.topics[0])
        topic_combo = ttk.Combobox(publish_frame, textvariable=self.topic_var,
                                   values=self.topics, state="readonly", width=50)
        topic_combo.grid(row=0, column=1, sticky="ew", padx=5)
        topic_combo.bind("<<ComboboxSelected>>", self._on_topic_selected)

        # Payload
        ttk.Label(publish_frame, text="Payload (JSON):").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.payload_text = tk.Text(publish_frame, height=4, width=60)
        self.payload_text.grid(row=1, column=1, sticky="ew", padx=5)
        self._update_payload_text()

        # Buttons
        button_frame = ttk.Frame(publish_frame)
        button_frame.grid(row=2, column=1, sticky="e", padx=5, pady=5)
        ttk.Button(button_frame, text="Load Default", command=self._load_default_payload).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Publish", command=self._publish_message).pack(side="left", padx=2)

        # ===== SUBSCRIBE SECTION =====
        subscribe_frame = ttk.LabelFrame(main_frame, text="SUBSCRIBE TO TOPIC", padding="10")
        subscribe_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        subscribe_frame.columnconfigure(1, weight=1)

        # Topic selection
        ttk.Label(subscribe_frame, text="Topic:").grid(row=0, column=0, sticky="w", padx=5)
        self.subscribe_topic_var = tk.StringVar(value=self.topics[0])
        subscribe_combo = ttk.Combobox(subscribe_frame, textvariable=self.subscribe_topic_var,
                                       values=self.topics, state="readonly", width=50)
        subscribe_combo.grid(row=0, column=1, sticky="ew", padx=5)

        # Subscribe button
        button_frame2 = ttk.Frame(subscribe_frame)
        button_frame2.grid(row=0, column=2, sticky="e", padx=5)
        ttk.Button(button_frame2, text="Subscribe", command=self._subscribe_topic).pack(side="left", padx=2)
        ttk.Button(button_frame2, text="Auto-Subscribe All", command=self._auto_subscribe_all).pack(side="left", padx=2)
        ttk.Button(button_frame2, text="Unsubscribe", command=self._unsubscribe_topic).pack(side="left", padx=2)
        ttk.Button(button_frame2, text="Unsubscribe All", command=self._unsubscribe_all).pack(side="left", padx=2)

        # Active subscriptions
        ttk.Label(subscribe_frame, text="Active Subscriptions:").grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))
        self.subscriptions_var = tk.StringVar(value="None")
        subscriptions_label = ttk.Label(subscribe_frame, textvariable=self.subscriptions_var,
                                        foreground="blue", wraplength=600, justify="left")
        subscriptions_label.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5)

        # State heartbeat controls
        heartbeat_frame = ttk.LabelFrame(main_frame, text="STATE MONITORING", padding="10")
        heartbeat_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5, rowspan=2)

        ttk.Label(heartbeat_frame, text="Note: SERVICE_STATE is only published\nwhen state CHANGES (by design).\n\nTo see continuous updates, toggle\nheartbeat:", justify="left").pack(anchor="w", pady=5)

        self.heartbeat_var = tk.BooleanVar(value=False)
        heartbeat_check = ttk.Checkbutton(heartbeat_frame, text="Enable State Heartbeat",
                                          variable=self.heartbeat_var,
                                          command=self._toggle_state_heartbeat)
        heartbeat_check.pack(anchor="w", pady=5)

        # ===== LOG SECTION =====
        log_frame = ttk.LabelFrame(main_frame, text="RECEIVED MESSAGES LOG", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        ttk.Button(log_frame, text="Clear Log", command=self._clear_log).grid(row=1, column=0, sticky="e", pady=5)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

    def _on_topic_selected(self, event=None):
        """Update payload when topic is selected"""
        self._update_payload_text()

    def _update_payload_text(self):
        """Update the payload text field with default payload"""
        topic = self.topic_var.get()
        payload = self.sample_payloads.get(topic, {})
        self.payload_text.delete("1.0", tk.END)
        self.payload_text.insert("1.0", json.dumps(payload, indent=2))

    def _load_default_payload(self):
        """Load default payload for selected topic"""
        self._update_payload_text()

    def _publish_message(self):
        """Publish message to selected topic"""
        topic = self.topic_var.get()
        payload_str = self.payload_text.get("1.0", tk.END).strip()

        try:
            payload = json.loads(payload_str) if payload_str else {}
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Error parsing payload: {e}")
            return

        try:
            self.broker.publish(topic, payload)
            self._log_message(f"✓ Published to '{topic}'", "success")
        except Exception as e:
            messagebox.showerror("Publish Error", str(e))
            self._log_message(f"✗ Publish failed: {e}", "error")

    def _subscribe_topic(self):
        """Subscribe to selected topic"""
        topic = self.subscribe_topic_var.get()

        if topic in self.subscriptions:
            messagebox.showwarning("Already Subscribed", f"Already subscribed to '{topic}'")
            return

        def callback(msg):
            # Handle non-JSON-serializable objects (like numpy arrays)
            try:
                msg_str = json.dumps(msg)
            except TypeError:
                # For non-serializable objects, show type and basic info
                if hasattr(msg, 'shape'):  # numpy array
                    msg_str = f"ndarray shape={msg.shape} dtype={msg.dtype}"
                elif isinstance(msg, bytes):
                    msg_str = f"bytes (length={len(msg)})"
                else:
                    msg_str = f"{type(msg).__name__} object"

            self._log_message(f"[{topic}] {msg_str}", "received")

        try:
            self.broker.subscribe(topic, callback)
            self.subscriptions[topic] = callback
            self._update_subscriptions_label()
            self._log_message(f"✓ Subscribed to '{topic}'", "success")
        except Exception as e:
            messagebox.showerror("Subscribe Error", str(e))
            self._log_message(f"✗ Subscribe failed: {e}", "error")

    def _auto_subscribe_all(self):
        """Auto-subscribe to all VisionTopics"""
        subscribed_count = 0
        for topic in self.topics:
            if topic not in self.subscriptions:
                def callback(msg, t=topic):
                    # Handle non-JSON-serializable objects (like numpy arrays)
                    try:
                        msg_str = json.dumps(msg)
                    except TypeError:
                        # For non-serializable objects, show type and basic info
                        if hasattr(msg, 'shape'):  # numpy array
                            msg_str = f"ndarray shape={msg.shape} dtype={msg.dtype}"
                        elif isinstance(msg, bytes):
                            msg_str = f"bytes (length={len(msg)})"
                        else:
                            msg_str = f"{type(msg).__name__} object"

                    self._log_message(f"[{t}] {msg_str}", "received")

                try:
                    self.broker.subscribe(topic, callback)
                    self.subscriptions[topic] = callback
                    subscribed_count += 1
                except Exception as e:
                    self._log_message(f"✗ Failed to subscribe to '{topic}': {e}", "error")

        self._update_subscriptions_label()
        self._log_message(f"✓ Auto-subscribed to {subscribed_count} topics", "success")

    def _unsubscribe_topic(self):
        """Unsubscribe from selected topic"""
        topic = self.subscribe_topic_var.get()

        if topic not in self.subscriptions:
            messagebox.showwarning("Not Subscribed", f"Not subscribed to '{topic}'")
            return

        try:
            # Remove from tracking
            del self.subscriptions[topic]
            self._update_subscriptions_label()
            self._log_message(f"✓ Unsubscribed from '{topic}'", "success")
        except Exception as e:
            messagebox.showerror("Unsubscribe Error", str(e))
            self._log_message(f"✗ Unsubscribe failed: {e}", "error")

    def _unsubscribe_all(self):
        """Unsubscribe from all topics"""
        if not self.subscriptions:
            messagebox.showinfo("No Subscriptions", "Not subscribed to any topics")
            return

        unsubscribed_count = len(self.subscriptions)
        self.subscriptions.clear()
        self._update_subscriptions_label()
        self._log_message(f"✓ Unsubscribed from {unsubscribed_count} topics", "success")

    def _update_subscriptions_label(self):
        """Update the active subscriptions label"""
        if self.subscriptions:
            subs_text = ", ".join(self.subscriptions.keys())
        else:
            subs_text = "None"
        self.subscriptions_var.set(subs_text)

    def _log_message(self, message: str, level: str = "info"):
        """Add message to queue (thread-safe)"""
        self.message_queue.put(message)

    def _process_message_queue(self):
        """Process messages from queue and update GUI - runs in main thread"""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            except:
                break
        # Schedule next poll
        self.root.after(100, self._process_message_queue)

    def _start_queue_polling(self):
        """Start the queue polling mechanism"""
        self.root.after(100, self._process_message_queue)

    def _start_state_heartbeat(self):
        """Start periodic state heartbeat to monitor vision system state"""
        self._poll_state_heartbeat()

    def _toggle_state_heartbeat(self):
        """Toggle state heartbeat on/off"""
        self.state_heartbeat_enabled = self.heartbeat_var.get()
        if self.state_heartbeat_enabled:
            self._log_message("✓ State heartbeat ENABLED - republishing every 2 seconds", "success")
            self._poll_state_heartbeat()
        else:
            self._log_message("✓ State heartbeat DISABLED", "success")

    def _poll_state_heartbeat(self):
        """Periodically republish current state to simulate continuous heartbeat"""
        if self.state_heartbeat_enabled and VisionTopics.SERVICE_STATE in self.subscriptions:
            # Republish the default state payload to simulate heartbeat
            state_payload = self.sample_payloads[VisionTopics.SERVICE_STATE]
            self.broker.publish(VisionTopics.SERVICE_STATE, state_payload)

        if self.state_heartbeat_enabled:
            # Schedule next heartbeat
            self.root.after(2000, self._poll_state_heartbeat)

    def _clear_log(self):
        """Clear the log"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")


if __name__ == "__main__":
    broker = MessageBroker()

    root = tk.Tk()
    gui = TopicBrokerGUI(root, broker)

    # Run vision system in a separate thread (background)
    def run_vision_system():
        print("Starting Vision System...")
        vs = VisionSystem(message_broker=broker,
                          service=FakeSettingsService(initial_data=CameraSettings()))
        try:
            while True:
                _, img, _ = vs.run()
                if img is not None:
                    cv2.imshow("Vision System", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nQuitting vision system...")
                    root.quit()
                    break
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            root.quit()
        finally:
            cv2.destroyAllWindows()

    vision_thread = threading.Thread(target=run_vision_system, daemon=True)
    vision_thread.start()

    # Run GUI mainloop in main thread (required by tkinter)
    root.mainloop()
