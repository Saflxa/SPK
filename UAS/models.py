from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class tbl_gpu(Base):
    __tablename__ = 'tbl_gpu'
    nama_gpu: Mapped[str] = mapped_column(primary_key=True)
    clock_speed: Mapped[int] = mapped_column()
    bandwith: Mapped[int] = mapped_column()
    vram: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    series: Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"tbl_gpu(nama_gpu={self.nama_gpu!r}, clock_speed={self.clock_speed!r})"