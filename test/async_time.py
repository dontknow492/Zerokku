import asyncio


async def main():
    print("this is main")
    await  write(1)
    await write(2)

async def write(path):
    file.write("data")



asyncio.run(main())