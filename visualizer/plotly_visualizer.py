"""Plotly visualizer for Fly-in.

This module is display-only:
- no scheduling
- no pathfinding
- no simulation decision logic

It renders:
- graph zones and connections
- drones over turns (reconstructed timeline from SimulationState.moves)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go

from core.graph import Graph
from core.simulator import SimulationState
from models.enums import DroneState
from models.zone import Zone, ZoneCategory, ZoneType


@dataclass(frozen=True)
class _DroneRenderState:
    """Display snapshot for one drone at one turn."""
    drone_id: str
    state: str
    current_zone: str
    destination: Optional[str]
    x: float
    y: float


class PlotlyVisualizer:
    """Render Fly-in simulation with Plotly animation.

    Parameters
    ----------
    graph:
        Graph instance containing zones and connections.
    simulation_results:
        SimulationState returned by Simulator.run().
    start_zone:
        Optional explicit start zone name. If not provided, auto-detected.
    end_zone:
        Optional explicit end zone name. If not provided, auto-detected.
    animation_speed_ms:
        Delay between frames in milliseconds.
    title:
        Figure title.
    """

    _ZONE_TYPE_COLORS: Dict[ZoneType, str] = {
        ZoneType.NORMAL: "lightblue",
        ZoneType.RESTRICTED: "orange",
        ZoneType.BLOCKED: "gray",
        ZoneType.PRIORITY: "cyan",
    }

    _CATEGORY_OVERRIDE_COLORS: Dict[ZoneCategory, str] = {
        ZoneCategory.START_HUB: "green",
        ZoneCategory.END_HUB: "green",
    }

    _DRONE_COLOR = "#111111"

    def __init__(
        self,
        graph: Graph,
        simulation_results: SimulationState,
        start_zone: Optional[str] = None,
        end_zone: Optional[str] = None,
        animation_speed_ms: int = 600,
        title: str = "Fly-in Simulation",
    ) -> None:
        if not isinstance(graph, Graph):
            raise TypeError("graph must be an instance of Graph")
        if not isinstance(simulation_results, SimulationState):
            raise TypeError(
                "simulation_results must be SimulationState returned by Simulator.run()"
            )

        self._graph = graph
        self._state = simulation_results
        self._animation_speed_ms = animation_speed_ms
        self._title = title

        self._start_zone_name, self._end_zone_name = self._resolve_start_end(
            start_zone, end_zone
        )

        self._zone_occupancy_by_turn = self._compute_zone_occupancy_by_turn()
        self._turn_drone_states = self._build_turn_drone_states()

        self._fig = self._build_figure()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def show(self) -> None:
        """Display interactive figure."""
        self._fig.show()

    def save(self, output_path: str | Path) -> None:
        """Save interactive figure to HTML."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)

    @property
    def figure(self) -> go.Figure:
        """Get underlying Plotly figure."""
        return self._fig

    # ------------------------------------------------------------------ #
    # Build figure
    # ------------------------------------------------------------------ #

    def _build_figure(self) -> go.Figure:
        fig = go.Figure()

        # 1) Static connections
        fig.add_trace(self._build_connections_trace())

        # 2) Static zones by legend groups
        for label, zone_selector in self._zone_groups():
            trace = self._build_zone_trace(label, zone_selector)
            if trace is not None:
                fig.add_trace(trace)

        # 3) Dynamic drones (initial frame)
        initial_turn = self._turn_drone_states[0] if self._turn_drone_states else []
        fig.add_trace(self._build_drones_trace(initial_turn, showlegend=True))

        # 4) Frames
        fig.frames = self._build_frames()

        # 5) Controls + layout
        duration_turns = max(0, len(self._turn_drone_states) - 1)
        fig.update_layout(
            title=f"{self._title} — durée: {duration_turns} tour(s)",
            template="plotly_white",
            hovermode="closest",
            xaxis=dict(title="X", zeroline=False),
            yaxis=dict(title="Y", zeroline=False, scaleanchor="x", scaleratio=1),
            legend=dict(
                title="Légende",
                x=1.02,
                y=1.0,
                xanchor="left",
                yanchor="top",
            ),
            margin=dict(l=40, r=240, t=70, b=70),
            updatemenus=self._play_pause_controls(),
            sliders=self._slider_controls(),
            annotations=[self._stats_annotation(0)],
        )

        return fig

    def _build_connections_trace(self) -> go.Scatter:
        x_vals: List[Optional[float]] = []
        y_vals: List[Optional[float]] = []

        for conn in self._graph.connections:
            zone_a = self._graph.zones.get(conn.zone_a)
            zone_b = self._graph.zones.get(conn.zone_b)
            if zone_a is None or zone_b is None:
                continue

            x_vals.extend([zone_a.x, zone_b.x, None])
            y_vals.extend([zone_a.y, zone_b.y, None])

        return go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color="#bdc3c7", width=1.4),
            hoverinfo="skip",
            name="Connexions",
            showlegend=True,
        )

    def _zone_groups(self) -> List[tuple[str, Any]]:
        """Legend grouping with requested color semantics."""
        return [
            ("START", lambda z: z.category == ZoneCategory.START_HUB),
            ("END", lambda z: z.category == ZoneCategory.END_HUB),
            (
                "NORMAL",
                lambda z: (
                    z.category == ZoneCategory.HUB and z.zone_type == ZoneType.NORMAL
                ),
            ),
            ("RESTRICTED", lambda z: z.zone_type == ZoneType.RESTRICTED),
            ("BLOCKED", lambda z: z.zone_type == ZoneType.BLOCKED),
            ("PRIORITY", lambda z: z.zone_type == ZoneType.PRIORITY),
        ]

    def _build_zone_trace(self, label: str, zone_selector: Any) -> Optional[go.Scatter]:
        zones = [z for z in self._graph.zones.values() if zone_selector(z)]
        if not zones:
            return None

        x_vals = [z.x for z in zones]
        y_vals = [z.y for z in zones]
        texts = [z.name for z in zones]
        colors = [self._zone_color(z) for z in zones]

        # Occupancy from turn 0 snapshot
        occupancy_map = self._zone_occupancy_by_turn[0] if self._zone_occupancy_by_turn else {}

        custom_data = []
        for z in zones:
            custom_data.append(
                [
                    z.name,
                    z.category.value,
                    z.zone_type.value,
                    z.max_drones,
                    occupancy_map.get(z.name, 0),
                ]
            )

        return go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            text=texts,
            textposition="top center",
            marker=dict(
                size=14,
                color=colors,
                line=dict(color="#2c3e50", width=1),
            ),
            name=f"Zone: {label}",
            customdata=custom_data,
            hovertemplate=(
                "<b>Zone</b><br>"
                "Nom: %{customdata[0]}<br>"
                "Catégorie: %{customdata[1]}<br>"
                "Type: %{customdata[2]}<br>"
                "Capacité: %{customdata[3]}<br>"
                "Occupation (tour): %{customdata[4]}<extra></extra>"
            ),
            showlegend=True,
        )

    def _build_drones_trace(
        self,
        drones: List[_DroneRenderState],
        showlegend: bool,
    ) -> go.Scatter:
        custom_data = []
        for d in drones:
            custom_data.append(
                [d.drone_id, d.state, d.current_zone, d.destination or "N/A"]
            )

        return go.Scatter(
            x=[d.x for d in drones],
            y=[d.y for d in drones],
            mode="markers",
            marker=dict(
                size=11,
                color=self._DRONE_COLOR,
                symbol="diamond",
                line=dict(color="#ffffff", width=1),
            ),
            name="Drones",
            customdata=custom_data,
            hovertemplate=(
                "<b>Drone</b><br>"
                "ID: %{customdata[0]}<br>"
                "État: %{customdata[1]}<br>"
                "Zone actuelle: %{customdata[2]}<br>"
                "Destination: %{customdata[3]}<extra></extra>"
            ),
            showlegend=showlegend,
        )

    def _build_frames(self) -> List[go.Frame]:
        frames: List[go.Frame] = []

        for turn_idx, drones in enumerate(self._turn_drone_states):
            frame = go.Frame(
                name=str(turn_idx),
                data=[self._build_drones_trace(drones, showlegend=False)],
                traces=[self._drone_trace_index()],
                layout=go.Layout(annotations=[self._stats_annotation(turn_idx)]),
            )
            frames.append(frame)

        return frames

    def _play_pause_controls(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": self._animation_speed_ms, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ]

    def _slider_controls(self) -> List[Dict[str, Any]]:
        if not self._turn_drone_states:
            return []

        steps = []
        for i in range(len(self._turn_drone_states)):
            steps.append(
                {
                    "label": str(i),
                    "method": "animate",
                    "args": [
                        [str(i)],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 0, "redraw": True},
                            "transition": {"duration": 0},
                        },
                    ],
                }
            )

        return [
            {
                "active": 0,
                "x": 0.0,
                "y": -0.08,
                "len": 0.8,
                "xanchor": "left",
                "yanchor": "top",
                "currentvalue": {"visible": True, "prefix": "Tour: "},
                "steps": steps,
            }
        ]

    def _stats_annotation(self, turn_index: int) -> Dict[str, Any]:
        drones = (
            self._turn_drone_states[turn_index]
            if 0 <= turn_index < len(self._turn_drone_states)
            else []
        )

        arrived = 0
        moving = 0
        for d in drones:
            if d.state == DroneState.DELIVERED.value:
                arrived += 1
            else:
                moving += 1

        duration_turns = max(0, len(self._turn_drone_states) - 1)
        text = (
            f"<b>Tour:</b> {turn_index}<br>"
            f"<b>Arrivés:</b> {arrived}<br>"
            f"<b>En déplacement:</b> {moving}<br>"
            f"<b>Durée totale:</b> {duration_turns} tour(s)"
        )

        return {
            "xref": "paper",
            "yref": "paper",
            "x": 1.02,
            "y": 0.55,
            "xanchor": "left",
            "yanchor": "top",
            "align": "left",
            "showarrow": False,
            "text": text,
            "bordercolor": "#dfe6e9",
            "borderwidth": 1,
            "borderpad": 8,
            "bgcolor": "#ffffff",
            "font": {"size": 12},
        }

    # ------------------------------------------------------------------ #
    # Timeline reconstruction (display-only)
    # ------------------------------------------------------------------ #

    def _build_turn_drone_states(self) -> List[List[_DroneRenderState]]:
        """Rebuild per-turn drone display states from SimulationState.moves."""
        drones = self._state.drones
        if not drones:
            return [[]]

        # Track current zone index inside each drone.path. SimulationState
        # stores drones after the run, so drone.current_zone is final state;
        # visual reconstruction must start from the first path zone.
        path_index_by_drone: Dict[str, int] = {}
        for drone in drones:
            path_index_by_drone[drone.drone_id] = 0

        # Turn 0: initial snapshot
        turn_states: List[List[_DroneRenderState]] = []
        turn_states.append(self._snapshot_from_indices(path_index_by_drone))

        # Next turns from scheduling moves
        for scheduling_result in self._state.moves:
            for drone in drones:
                drone_id = drone.drone_id
                destination = scheduling_result.moves.get(drone_id)
                if destination is None:
                    continue

                if not drone.path:
                    continue

                # move index forward to destination if found in remaining path
                current_idx = path_index_by_drone[drone_id]
                remaining = drone.path[current_idx:]
                if destination in remaining:
                    jump = remaining.index(destination)
                    path_index_by_drone[drone_id] = current_idx + jump
                elif destination in drone.path:
                    path_index_by_drone[drone_id] = drone.path.index(destination)

            turn_states.append(self._snapshot_from_indices(path_index_by_drone))

        return turn_states

    def _snapshot_from_indices(
        self,
        path_index_by_drone: Dict[str, int],
    ) -> List[_DroneRenderState]:
        """Build a display snapshot for all drones."""
        snapshot: List[_DroneRenderState] = []

        for drone in self._state.drones:
            drone_id = drone.drone_id
            idx = path_index_by_drone.get(drone_id, 0)

            current_zone_name = self._safe_path_zone(drone.path, idx, fallback=self._start_zone_name)
            destination = self._safe_path_zone(drone.path, idx + 1, fallback=None)

            zone = self._graph.zones.get(current_zone_name)
            if zone is None:
                # fallback defensive
                x, y = 0.0, 0.0
            else:
                x, y = float(zone.x), float(zone.y)

            state_value = self._infer_drone_state(current_zone_name, destination)

            snapshot.append(
                _DroneRenderState(
                    drone_id=drone_id,
                    state=state_value,
                    current_zone=current_zone_name,
                    destination=destination,
                    x=x,
                    y=y,
                )
            )

        return snapshot

    def _infer_drone_state(
        self,
        current_zone_name: str,
        destination: Optional[str],
    ) -> str:
        """Infer display state (visual-only label)."""
        if current_zone_name == self._end_zone_name:
            return DroneState.DELIVERED.value
        if destination is None:
            return DroneState.IDLE.value

        destination_zone = self._graph.zones.get(destination)
        if destination_zone and destination_zone.zone_type == ZoneType.RESTRICTED:
            return DroneState.IN_TRANSIT_RESTRICTED.value

        return DroneState.MOVING.value

    # ------------------------------------------------------------------ #
    # Occupancy computation for zone hover (display-only)
    # ------------------------------------------------------------------ #

    def _compute_zone_occupancy_by_turn(self) -> List[Dict[str, int]]:
        """Compute occupancy map for each turn from reconstructed snapshots."""
        occupancy_per_turn: List[Dict[str, int]] = []

        # temporarily build timeline if not ready yet
        temp_timeline = self._build_turn_drone_states_for_occupancy()

        for turn_drones in temp_timeline:
            occupancy: Dict[str, int] = {}
            for d in turn_drones:
                occupancy[d.current_zone] = occupancy.get(d.current_zone, 0) + 1
            occupancy_per_turn.append(occupancy)

        return occupancy_per_turn

    def _build_turn_drone_states_for_occupancy(self) -> List[List[_DroneRenderState]]:
        """Build timeline without using self._turn_drone_states to avoid init cycle."""
        drones = self._state.drones
        if not drones:
            return [[]]

        path_index_by_drone: Dict[str, int] = {}
        for drone in drones:
            path_index_by_drone[drone.drone_id] = 0

        timeline: List[List[_DroneRenderState]] = []
        timeline.append(self._snapshot_from_indices(path_index_by_drone))

        for scheduling_result in self._state.moves:
            for drone in drones:
                drone_id = drone.drone_id
                destination = scheduling_result.moves.get(drone_id)
                if destination is None or not drone.path:
                    continue

                current_idx = path_index_by_drone[drone_id]
                remaining = drone.path[current_idx:]
                if destination in remaining:
                    path_index_by_drone[drone_id] = current_idx + remaining.index(destination)
                elif destination in drone.path:
                    path_index_by_drone[drone_id] = drone.path.index(destination)

            timeline.append(self._snapshot_from_indices(path_index_by_drone))

        return timeline

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _resolve_start_end(
        self,
        start_zone: Optional[str],
        end_zone: Optional[str],
    ) -> tuple[str, str]:
        """Resolve start/end zone names."""
        detected_start = start_zone
        detected_end = end_zone

        if detected_start is None:
            for z in self._graph.zones.values():
                if z.category == ZoneCategory.START_HUB:
                    detected_start = z.name
                    break

        if detected_end is None:
            for z in self._graph.zones.values():
                if z.category == ZoneCategory.END_HUB:
                    detected_end = z.name
                    break

        if detected_start is None:
            detected_start = next(iter(self._graph.zones.keys()))
        if detected_end is None:
            detected_end = next(reversed(self._graph.zones.keys()))

        return detected_start, detected_end

    def _zone_color(self, zone: Zone) -> str:
        """Choose color according to requested semantics."""
        if zone.color:
            return zone.color
        if zone.category in self._CATEGORY_OVERRIDE_COLORS:
            return self._CATEGORY_OVERRIDE_COLORS[zone.category]
        return self._ZONE_TYPE_COLORS.get(zone.zone_type, "lightblue")

    def _drone_trace_index(self) -> int:
        """Trace index where dynamic drone layer is stored."""
        # [connections] + zone group traces + [drones]
        zone_trace_count = 0
        for _, selector in self._zone_groups():
            if any(selector(z) for z in self._graph.zones.values()):
                zone_trace_count += 1
        return 1 + zone_trace_count

    @staticmethod
    def _safe_path_zone(path: List[str], index: int, fallback: Optional[str]) -> str:
        """Safe path lookup with fallback."""
        if 0 <= index < len(path):
            return path[index]
        if fallback is None:
            return ""
        return fallback
