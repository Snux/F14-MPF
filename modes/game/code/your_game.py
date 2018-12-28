import asyncio

from mpf.modes.game.code.game import Game

class YourGame(Game):

    @asyncio.coroutine
    def _start_ball(self, is_extra_ball=False):
        """Perform ball start procedure.

        Note this method is called for each ball that starts, even if it's
        after a Shoot Again scenario for the same player.

        Posts a queue event called *ball_starting*, giving other modules the
        opportunity to do things before the ball actually starts. Once that
        event is clear, this method calls :meth:`ball_started`.
        """
        event_args = {
            "player": self.player.number,
            "ball": self.player.ball,
            "balls_remaining": self.balls_per_game - self.player.ball,
            "is_extra_ball": is_extra_ball}

        self.debug_log("***************************************************")
        self.debug_log("****************** BALL STARTING ******************")
        self.debug_log("**                                               **")
        self.debug_log("**    Player: {}    Ball: {}   Score: {}".format(self.player.number,
                                                                         self.player.ball,
                                                                         self.player.score
                                                                         ).ljust(49) + '**')
        self.debug_log("**                                               **")
        self.debug_log("***************************************************")
        self.debug_log("***************************************************")

        yield from self.machine.events.post_async('ball_will_start', **event_args)
        '''event: ball_will_start
        desc: The ball is about to start. This event is posted just before
        :doc:`ball_starting`.'''

        yield from self.machine.events.post_queue_async('ball_starting', **event_args)
        '''event: ball_starting
        desc: A ball is starting. This is a queue event, so the ball won't
        actually start until the queue is cleared.'''

        # register handlers to watch for ball drain and live ball removed
        self.add_mode_event_handler('ball_drain', self.ball_drained)

        self.balls_in_play = 1

        self.debug_log("ball_started for Ball %s", self.player.ball)

        yield from self.machine.events.post_async('ball_started', **event_args)
        '''event: ball_started
        desc: A new ball has started.
        args:
        ball: The ball number.
        player: The player number.'''

        if self.num_players == 1:
            yield from self.machine.events.post_async('single_player_ball_started')
            '''event: single_player_ball_started
            desc: A new ball has started, and this is a single player game.'''
        else:
            yield from self.machine.events.post_async('multi_player_ball_started')
            '''event: multi_player_ball_started
            desc: A new ball has started, and this is a multiplayer game.'''
            yield from self.machine.events.post_async(
                'player_{}_ball_started'.format(self.player.number))
            '''event player_(number)_ball_started
            desc: A new ball has started, and this is a multiplayer game.
            The player number is the (number) in the event that's posted.'''

        if not hasattr(self.machine, "playfield") or not self.machine.playfield:
            raise AssertionError("The game did not define default playfield. Did you add tags: default to one of your "
                                 "playfield?")

        # add some logic here to determine the source device
        self.machine.playfield.add_ball(player_controlled=True, source_device=self.machine.ball_devices['bd_lock2'])
