# Copyright 2021 AIT Austrian Institute of Technology GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import re
from rosbag2_py import BagMetadata
from typing import Sequence, Tuple
from datetime import date, timedelta, datetime, timezone, time
from rclpy.time import Duration, Time, CONVERSION_CONSTANT


def datetime_to_ros_time(t: datetime) -> Time:
    return Time(seconds=t.timestamp())


def ros_time_from_nanoseconds(ns) -> Time:
    time_s = int(ns / CONVERSION_CONSTANT)
    time_ns_only = ns % CONVERSION_CONSTANT
    return Time(seconds=time_s, nanoseconds=time_ns_only)


def ros_duration_from_nanoseconds(ns) -> Duration:
    duration_s = int(ns / CONVERSION_CONSTANT)
    duration_ns_only = ns % CONVERSION_CONSTANT
    return Duration(seconds=duration_s, nanoseconds=duration_ns_only)


def get_bag_bounds(metadatas: Sequence[BagMetadata]) -> Tuple[datetime, datetime]:
    total_start = datetime.max.replace(tzinfo=timezone.utc)
    total_end = datetime.min.replace(tzinfo=timezone.utc)
    for metadata in metadatas:
        starting_time_utc = metadata.starting_time.astimezone(timezone.utc)
        end_time = starting_time_utc + metadata.duration
        if starting_time_utc < total_start:
            total_start = starting_time_utc
        if end_time > total_end:
            total_end = end_time
    return (total_start, total_end)


def ros_to_datetime_utc(ros_time: Time):
    (secs, nanosecs) = ros_time.seconds_nanoseconds()
    return datetime.fromtimestamp(secs + nanosecs / CONVERSION_CONSTANT, tz=timezone.utc)


def add_daytime(t: date, day_time: time) -> datetime:
    """Combine date of t with day_time to a datetime object."""
    min_utc = datetime.min.replace(tzinfo=timezone.utc)
    utc_day_time = datetime.combine(t, min_utc.time(), tzinfo=timezone.utc)
    day_offset = datetime.combine(date.min, day_time, tzinfo=timezone.utc) - min_utc
    return utc_day_time + day_offset


def is_same_day(date1: datetime, date2: datetime) -> bool:
    return date1.date() == date2.date()


def DurationType(values):
    try:
        seconds = float(values)
        if seconds < 0:
            raise argparse.ArgumentTypeError("duration must be positive")
        return timedelta(seconds=seconds)
    except ValueError:
        raise argparse.ArgumentTypeError("duration must be float (in seconds)")


def DayTimeType(values):
    try:
        match = re.findall(r"(\d+):(\d+):(\d+):(\d+)", values)
        if len(match) == 0:
            match = re.findall(r"(\d+):(\d+):(\d+)", values)
        if len(match) == 0:
            match = re.findall(r"(\d+):(\d+)", values)
        if len(match) == 0:
            raise argparse.ArgumentTypeError("pass daytime as hh:mm[:ss[:ms]]")

        if len(match[0]) < 2 or len(match[0]) > 4:
            raise argparse.ArgumentTypeError("pass daytime as hh:mm[:ss[:ms]]")

        ms = 0
        s = 0
        h = int(match[0][0])
        m = int(match[0][1])
        if len(match[0]) >= 3:
            s = int(match[0][2])
        if len(match[0]) >= 4:
            ms = int(match[0][3])

        if h < 0 or h > 23:
            raise argparse.ArgumentTypeError("hour between 0 and 23")
        if m < 0 or m > 59:
            raise argparse.ArgumentTypeError("minute between 0 and 59")
        if s < 0 or s > 59:
            raise argparse.ArgumentTypeError("second between 0 and 59")
        if ms < 0 or ms > 999:
            raise argparse.ArgumentTypeError("millisecond between 0 and 999")

        return time(h, m, s, ms * 1000, tzinfo=timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError("duration must be float (in seconds)")


def DurationOrDayTimeType(values):
    try:
        return DayTimeType(values)
    except argparse.ArgumentTypeError:
        return DurationType(values)
