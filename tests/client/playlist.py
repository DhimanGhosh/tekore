from asyncio import run

from tests._cred import TestCaseWithUserCredentials, TestCaseWithCredentials
from ._resources import (
    user_id,
    playlist_id,
    playlist_local,
    playlist_podcast,
    track_ids,
    image,
)

from tekore.client.api import SpotifyPlaylist


class TestSpotifyPlaylistView(TestCaseWithCredentials):
    def test_playlists(self):
        self.client.playlists(user_id)

    def test_playlist(self):
        playlist = self.client.playlist(playlist_id)
        self.assertEqual(playlist.id, playlist_id)

    def test_playlist_track_has_episode_and_track(self):
        track = self.client.playlist(playlist_id).tracks.items[0].track
        self.assertTrue(all(i is not None for i in (track.episode, track.track)))

    def test_playlist_owner_attributes(self):
        owner = self.client.playlist(playlist_id).owner
        nones = [i is None for i in (owner.followers, owner.images)]
        self.assertTrue(all(nones))

    def test_playlist_with_local_track(self):
        playlist = self.client.playlist(playlist_local)
        self.assertTrue(playlist.tracks.items[0].is_local)

    def test_playlist_cover_image(self):
        self.client.playlist_cover_image(playlist_id)

    def test_playlist_tracks(self):
        tracks = self.client.playlist_tracks(playlist_id)
        self.assertGreater(tracks.total, 0)

    def test_async_playlist_tracks(self):
        async def f():
            client = SpotifyPlaylist(self.app_token, asynchronous=True)
            return await client.playlist_tracks(playlist_id)

        tracks = run(f())
        self.assertGreater(tracks.total, 0)

    def test_playlist_with_fields_returns_object(self):
        playlist = self.client.playlist(playlist_id, fields='uri')
        self.assertIsInstance(playlist, dict)

    def test_async_playlist_with_fields_returns_object(self):
        async def f():
            client = SpotifyPlaylist(self.app_token, asynchronous=True)
            return await client.playlist(playlist_id, fields='uri')

        playlist = run(f())
        self.assertIsInstance(playlist, dict)

    def test_playlist_tracks_with_fields_returns_object(self):
        tracks = self.client.playlist_tracks(playlist_id, fields='total')
        self.assertIsInstance(tracks, dict)

    def test_async_playlist_tracks_with_fields_returns_object(self):
        async def f():
            client = SpotifyPlaylist(self.app_token, asynchronous=True)
            return await client.playlist_tracks(playlist_id, fields='uri')

        tracks = run(f())
        self.assertIsInstance(tracks, dict)

    def test_playlist_podcast_no_market_returns_none(self):
        playlist = self.client.playlist(playlist_podcast)
        self.assertIsNone(playlist.tracks.items[0].track)

    def test_playlist_podcast_with_market_returned(self):
        playlist = self.client.playlist(playlist_podcast, market='FI')
        self.assertTrue(playlist.tracks.items[0].track.episode)

    def test_playlist_with_podcast_as_tracks_no_market_returns_object(self):
        playlist = self.client.playlist(playlist_podcast, episodes_as_tracks=True)
        self.assertIsNone(playlist['tracks']['items'][0]['track'])

    def test_playlist_with_podcast_as_tracks_with_market_returns_object(self):
        playlist = self.client.playlist(
            playlist_podcast,
            market='FI',
            episodes_as_tracks=True
        )
        self.assertTrue(playlist['tracks']['items'][0]['track']['track'])

    def test_playlist_tracks_podcast_no_market_returns_none(self):
        tracks = self.client.playlist_tracks(playlist_podcast)
        self.assertIsNone(tracks.items[0].track)

    def test_playlist_tracks_podcast_with_market_returned(self):
        tracks = self.client.playlist_tracks(playlist_podcast, market='FI')
        self.assertTrue(tracks.items[0].track.episode)

    def test_playlist_tracks_with_podcast_as_tracks_no_market_returns_object(self):
        tracks = self.client.playlist_tracks(
            playlist_podcast,
            episodes_as_tracks=True
        )
        self.assertIsNone(tracks['items'][0]['track'])

    def test_playlist_tracks_with_podcast_as_tracks_with_market_returns_object(self):
        tracks = self.client.playlist_tracks(
            playlist_podcast,
            market='FI',
            episodes_as_tracks=True
        )
        self.assertTrue(tracks['items'][0]['track']['track'])


class TestSpotifyPlaylistViewAsUser(TestCaseWithUserCredentials):
    def test_followed_playlists(self):
        self.client.followed_playlists()

    def test_playlist_with_podcast(self):
        playlist = self.client.playlist(playlist_podcast)
        self.assertEqual(playlist.id, playlist_podcast)

    def test_playlist_tracks_with_podcast(self):
        playlist = self.client.playlist(playlist_podcast)
        self.assertEqual(playlist.id, playlist_podcast)


class TestSpotifyPlaylistModify(TestCaseWithUserCredentials):
    """
    Ordered test set to test playlist creation and modification.
    """
    def assertTracksEqual(self, sub_test_msg: str, playlist: str, tracks: list):
        observed = self.client.playlist_tracks(playlist)
        with self.subTest(sub_test_msg):
            self.assertListEqual(
                [t.track.id for t in observed.items],
                tracks
            )

    def test_playlist_modifications(self):
        playlist = self.client.playlist_create(
            self.current_user_id,
            'tekore-test',
            public=False,
            description='Temporary test playlist for Tekore'
        )
        with self.subTest('Playlist created'):
            self.assertIsNotNone(playlist)

        try:
            # Upload new cover, assert last to wait for server
            self.client.playlist_cover_image_upload(playlist.id, image)

            new_name = 'tekore-test-modified'
            self.client.playlist_change_details(
                playlist.id,
                name=new_name,
                description='Temporary test playlist for Tekore (modified)'
            )
            playlist = self.client.playlist(playlist.id)
            with self.subTest('Details changed'):
                self.assertEqual(playlist.name, new_name)

            self.client.playlist_tracks_add(playlist.id, track_ids[::-1])
            self.assertTracksEqual('Tracks added', playlist.id, track_ids[::-1])

            self.client.playlist_tracks_replace(playlist.id, track_ids)
            self.assertTracksEqual('Tracks replaced', playlist.id, track_ids)

            # Note: reordering tracks can sometimes result in another version of
            # the track to be added to the playlist instead. This occurred with
            # a 'single' being converted to the album version.
            snapshot = self.client.playlist_tracks_reorder(
                playlist.id,
                range_start=1,
                insert_before=0
            )
            self.assertTracksEqual(
                'Tracks reordered',
                playlist.id,
                [track_ids[1], track_ids[0]] + track_ids[2:]
            )

            self.client.playlist_tracks_reorder(
                playlist.id,
                range_start=1,
                insert_before=0,
                snapshot_id=snapshot
            )
            self.assertTracksEqual(
                'Tracks reordered with snapshot',
                playlist.id,
                track_ids
            )

            self.client.playlist_tracks_remove(playlist.id, track_ids)
            tracks = self.client.playlist_tracks(playlist.id)
            with self.subTest('Tracks removed'):
                self.assertEqual(tracks.total, 0)

            # Add tracks back with duplicates and test removing occurrences
            new_tracks = track_ids + track_ids[::-1]
            self.client.playlist_tracks_replace(playlist.id, new_tracks)
            self.client.playlist_tracks_remove_occurrences(
                playlist.id,
                [(id_, ix) for ix, id_ in enumerate(track_ids)]
            )
            self.assertTracksEqual(
                'Occurrences removed',
                playlist.id,
                track_ids[::-1]
            )

            # Add tracks back with duplicates and test removing indices
            new_tracks = track_ids + track_ids[::-1]
            self.client.playlist_tracks_replace(playlist.id, new_tracks)
            playlist = self.client.playlist(playlist.id)
            self.client.playlist_tracks_remove_indices(
                playlist.id,
                list(range(len(track_ids))),
                playlist.snapshot_id
            )
            self.assertTracksEqual('Indices removed', playlist.id, track_ids[::-1])

            self.client.playlist_tracks_clear(playlist.id)
            self.assertTracksEqual('Tracks cleared', playlist.id, [])

            # Assert cover was uploaded
            cover = self.client.playlist_cover_image(playlist.id)
            with self.subTest('Cover uploaded'):
                self.assertGreater(len(cover), 0)
        except Exception:
            raise
        finally:
            # Unfollow (delete) playlist to tear down
            self.client.playlist_unfollow(playlist.id)
