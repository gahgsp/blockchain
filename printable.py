class Printable:

    def __repr__(self):
        """
        Defines what to show when printing a instance of this class.
        :return: the String representation of this class.
        """
        return str(self.__dict__)