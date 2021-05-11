INITIAL_FRAME=-1

function g_framecount()
    if(INITIAL_FRAME == -1)
    then
        INITIAL_FRAME = fba.framecount()
    end
    TOTAL_FRAMES = fba.framecount() - INITIAL_FRAME
    --print(TOTAL_FRAMES)
    if TOTAL_FRAMES % 60 == 0 then
        SECONDS=TOTAL_FRAMES/60
        print(SECONDS)
        file = io.open("framecount.txt", "w")
        file:write(SECONDS)
        file:close()
    end
end

-- Frame count doesn't reset after f3
emu.registerafter(function() g_framecount() end)