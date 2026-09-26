"""A tiny, cancellable timeline for animated lessons.

Scenes are ordinary ``async`` functions. Every pause and every screen
update goes through the Timeline, which gives three guarantees:

* **Cancel anywhere.** Each run gets a generation number. Pausing,
  jumping to another chapter, editing the kernel or clicking a pixel
  bumps the generation; the old scene notices at its next wait or
  update and stops cleanly (``Cancelled``), so two scenes never fight
  over the same controls.
* **One speed knob.** Waits and animation durations are divided by
  ``speed``, so the speed slider scales the whole lesson.
* **Safe when hidden.** If a control can no longer update (the user
  navigated away), the run is cancelled instead of raising.
"""

import asyncio


class Cancelled(Exception):
    """Raised inside a scene when its run has been superseded."""


class Timeline:
    TICK = 0.05  # long waits are sliced so a pause reacts within ~50 ms

    def __init__(self, page, on_state_change=None):
        self.page = page
        self.on_state_change = on_state_change
        self.generation = 0
        self.speed = 1.0
        self.running = False

    # ---------------------------------------------------------
    # RUN CONTROL
    # ---------------------------------------------------------

    def start(self, scene_factory):
        """Cancel whatever is playing and run scene_factory(gen)."""
        self.cancel(notify=False)
        generation = self.generation
        self.running = True
        self._notify()

        async def runner():
            try:
                await scene_factory(generation)
            except Cancelled:
                pass
            finally:
                if generation == self.generation:
                    self.running = False
                    self._notify()

        self.page.run_task(runner)

    def cancel(self, notify=True):
        self.generation += 1
        was_running = self.running
        self.running = False
        if notify and was_running:
            self._notify()

    def alive(self, generation):
        return generation == self.generation

    def check(self, generation):
        if generation != self.generation:
            raise Cancelled()

    def _notify(self):
        if self.on_state_change:
            try:
                self.on_state_change(self.running)
            except Exception:
                pass

    # ---------------------------------------------------------
    # TIME
    # ---------------------------------------------------------

    def ms(self, milliseconds):
        """Animation duration scaled by the current speed."""
        return max(1, int(milliseconds / self.speed))

    async def wait(self, generation, seconds):
        """Speed-scaled pause that aborts promptly when cancelled."""
        self.check(generation)
        remaining = seconds / self.speed

        while remaining > 0:
            step = min(self.TICK, remaining)
            await asyncio.sleep(step)
            remaining -= step
            self.check(generation)

    async def frame(self, generation):
        """Let Flutter render one frame (used before starting a move)."""
        await asyncio.sleep(0.03)
        self.check(generation)

    # ---------------------------------------------------------
    # UPDATES
    # ---------------------------------------------------------

    def push(self, generation, *controls):
        """Update controls, or cancel the run if they are gone."""
        self.check(generation)
        for control in controls:
            try:
                control.update()
            except Exception:
                self.cancel()
                raise Cancelled()
