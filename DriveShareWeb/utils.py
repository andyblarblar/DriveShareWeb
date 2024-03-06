class TimeRange(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.duration = self.end - self.start

    def is_overlapped(self, time_range):
        if max(self.start, time_range.start) < min(self.end, time_range.end):
            return True
        else:
            return False

    def get_overlapped_range(self, time_range):
        if not self.is_overlapped(time_range):
            return

        if time_range.start >= self.start:
            if self.end >= time_range.end:
                return TimeRange(time_range.start, time_range.end)
            else:
                return TimeRange(time_range.start, self.end)
        elif time_range.start < self.start:
            if time_range.end >= self.end:
                return TimeRange(self.start, self.end)
            else:
                return TimeRange(self.start, time_range.end)
